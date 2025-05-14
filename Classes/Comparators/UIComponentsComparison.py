from difflib import SequenceMatcher
from itertools import product

class UIComponentsComparison():
    def __init__(self, baseline_uihierarchy, actual_uihierarchy):
        # Initializes the UIComponentsComparison object and performs correlation between UI components from the baseline and actual hierarchies
        baseline_uicomponents = baseline_uihierarchy.list_all_components()
        actual_uicomponents = actual_uihierarchy.list_all_components()
        self.correlation = self.establish_correlations(baseline_uicomponents, actual_uicomponents)


    def similarity_score(self, str1, str2):
        """
        Computes the similarity ratio between two strings using the SequenceMatcher.

        :param str1: First string to compare.
        :param str2: Second string to compare.
        :return: Float between 0 and 1 representing the similarity ratio.
        """
        return SequenceMatcher(None, str1, str2).ratio()

    def overlap(self, bounds1, bounds2):
        """
        Computes the Intersection over Union (IoU) between two bounding boxes.

        :param bounds1: Tuple or list of four integers [x1, y1, x2, y2].
        :param bounds2: Tuple or list of four integers [x1, y1, x2, y2].
        :return: Float between 0 and 1 representing the IoU, or 0 if invalid input.
        """
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
        """
        Establishes correlations between baseline and actual UI components by
        computing similarity scores based on text, class, content-desc, and bounds.

        :param baseline: List of UI components from the baseline hierarchy.
        :param actual: List of UI components from the actual hierarchy.
        :return: A dictionary mapping baseline component line numbers to actual ones or "Unrelated".
        """
        pairs = []

        # Generate all possible pairs and compute their similarity score
        for b, a in product(baseline, actual):
            dict1=b.as_dict()
            dict2=a.as_dict()

            text_sim = self.similarity_score(str(dict1.get('text', '')), str(dict2.get('text', '')))
            class_sim = self.similarity_score(str(dict1.get('class', '')), str(dict2.get('class', '')))
            desc_sim = self.similarity_score(str(dict1.get('content-desc', '')), str(dict2.get('content-desc', '')))

            try:
                bounds1 = eval(dict1['bounds']) if isinstance(dict1['bounds'], str) else dict1['bounds']
                bounds2 = eval(dict2['bounds']) if isinstance(dict2['bounds'], str) else dict2['bounds']
                bounds_sim = self.overlap(bounds1, bounds2)
            except:
                bounds_sim = 0  # Handle invalid or missing bounds

            # Weighted total score
            total_score = 0.5 * text_sim + 0.2 * class_sim + 0.2 * desc_sim + 0.1 * bounds_sim

            pairs.append((b, a, total_score))

        # Sort all pairs by similarity score in descending order
        pairs.sort(key=lambda x: x[2], reverse=True)
        correlation = {}
        used_baseline = set()
        used_actual = set()

        # Select the best non-conflicting matches
        for b, a, score in pairs:
            if b.sourceLine not in used_baseline and a.sourceLine not in used_actual:
                correlation[b.sourceLine] = a.sourceLine
                b.addCorrelation({"UIComponent": a, "Score": score})
                a.addCorrelation({"UIComponent": b, "Score": score})
                used_baseline.add(b.sourceLine)
                used_actual.add(a.sourceLine)

        # Mark unmatched baseline components as "Unrelated"
        for item in baseline:
            dictionary=item.as_dict()
            if dictionary['line'] not in used_baseline:
                correlation[dictionary['line']] = "Unrelated"
                b.addCorrelation({"UIComponent": "Unrelated", "Score": 0.0})

        # Mark unmatched actual components as "Unrelated"
        for item in actual:
            dictionary=item.as_dict()
            if dictionary['line'] not in used_actual:
                correlation['Unrelated'] = dictionary['line']
                a.addCorrelation({"UIComponent": "Unrelated", "Score": 0.0})

        return correlation