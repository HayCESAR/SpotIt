from difflib import SequenceMatcher
from itertools import product

class UIComponentsComparison():
    def __init__(self, baseline_uihierarchy, actual_uihierarchy):
        baseline_uicomponents = baseline_uihierarchy.list_all_components()
        actual_uicomponents = actual_uihierarchy.list_all_components()
        self.correlation = self.establish_correlations(baseline_uicomponents, actual_uicomponents)


    def similarity_score(self, str1, str2):
        """Compute a similarity score between two strings."""
        return SequenceMatcher(None, str1, str2).ratio()

    def overlap(self, bounds1, bounds2):
        """Compute the overlap ratio of two bounding boxes."""
        if not (isinstance(bounds1, (list, tuple)) and isinstance(bounds2, (list, tuple)) and len(bounds1) == 4 and len(bounds2) == 4):
            return 0

        x1_min, y1_min, x1_max, y1_max = bounds1
        x2_min, y2_min, x2_max, y2_max = bounds2

        # Find the intersection
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))

        intersection = x_overlap * y_overlap
        area1 = (x1_max - x1_min) * (y1_max - y1_min)
        area2 = (x2_max - x2_min) * (y2_max - y2_min)

        union = area1 + area2 - intersection

        return intersection / union if union else 0

    def establish_correlations(self, baseline, actual):
        """Establish correlations between baseline and actual lists of dictionaries."""
        pairs = []
        used = set()

        for b, a in product(baseline, actual):
            dict1=b.as_dict()
            dict2=a.as_dict()
            if dict1['line'] in used or dict2['line'] in used:
                continue

            text_sim = self.similarity_score(str(dict1.get('text', '')), str(dict2.get('text', '')))
            class_sim = self.similarity_score(str(dict1.get('class', '')), str(dict2.get('class', '')))
            desc_sim = self.similarity_score(str(dict1.get('content-desc', '')), str(dict2.get('content-desc', '')))

            try:
                bounds1 = eval(dict1['bounds']) if isinstance(dict1['bounds'], str) else dict1['bounds']
                bounds2 = eval(dict2['bounds']) if isinstance(dict2['bounds'], str) else dict2['bounds']
                bounds_sim = self.overlap(bounds1, bounds2)
            except:
                bounds_sim = 0  # Default to 0 if parsing fails

            total_score = 0.4 * text_sim + 0.2 * class_sim + 0.2 * desc_sim + 0.2 * bounds_sim

            pairs.append((b, a, total_score))

        pairs.sort(key=lambda x: x[2], reverse=True)
        correlation = {}
        used_baseline = set()
        used_actual = set()

        for b, a, score in pairs:
            if b.sourceLine not in used_baseline and a.sourceLine not in used_actual:
                correlation[b.sourceLine] = a.sourceLine
                b.addCorrelation({"UIComponent": a, "Score": score})
                a.addCorrelation({"UIComponent": b, "Score": score})
                used_baseline.add(b.sourceLine)
                used_actual.add(a.sourceLine)

        # Assign "Unrelated" to unmatched items
        for item in baseline:
            dictionary=item.as_dict()
            if dictionary['line'] not in used_baseline:
                correlation[dictionary['line']] = "Unrelated"
                b.addCorrelation({"UIComponent": "Unrelated", "Score": 0.0})

        for item in actual:
            dictionary=item.as_dict()
            if dictionary['line'] not in used_actual:
                correlation['Unrelated'] = dictionary['line']
                a.addCorrelation({"UIComponent": "Unrelated", "Score": 0.0})

        return correlation