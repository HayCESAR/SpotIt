from Classes.Screenshot import Screenshot
from Classes.Comparators.ImageComparison import ImageComparison

class Oracle:
    def __init__(self, baseline, actual, uicomponents_in_difference_zones):
        self.baseline = baseline
        self.actual = actual
        self.uicomponents_in_difference_zones = uicomponents_in_difference_zones
        self.tips = []

    def getTips(self):
        wanted_missing = []
        wanted_added = []

        for zone_key, zone_data in self.uicomponents_in_difference_zones.items():
            self._processBaselineComponents(zone_key, zone_data['baseline'], zone_data['actual'], wanted_missing, wanted_added)
            self._processActualComponents(zone_key, zone_data['actual'], zone_data['baseline'], wanted_missing, wanted_added)

        return self.tips

    def _processBaselineComponents(self, key, baseline_components, actual_components, wanted_missing, wanted_added):
        for component in baseline_components:
            if not component:
                continue
            if not component.correlation:
                self._addTip(key, component, "Unrelated", "UI Component missing")
            elif component.correlation["UIComponent"] not in actual_components:
                if component in wanted_added:
                    wanted_added.remove(component)
                    self._identifyChanges(key, component)
                else:
                    wanted_missing.append(component.correlation["UIComponent"])
            else:
                self._identifyChanges(key, component)

    def _processActualComponents(self, key, actual_components, baseline_components, wanted_missing, wanted_added):
        for component in actual_components:
            if not component:
                continue
            if not component.correlation:
                self._addTip(key, "Unrelated", component, "UI Component added")
            elif component.correlation["UIComponent"] not in baseline_components:
                if component in wanted_missing:
                    wanted_missing.remove(component)
                    self._identifyChanges(key, component.correlation["UIComponent"])
                else:
                    wanted_added.append(component.correlation["UIComponent"])

    def _identifyChanges(self, key, component):
        counterpart = component.correlation["UIComponent"]
        changes = self._compareProperties(component, counterpart)
        for change in changes:
            self._addTip(
                key, component, counterpart,
                f"{change['Property']} changed",
                change['Baseline Value'], change['Actual Value']
            )

    def _compareProperties(self, baseline, actual):
        dom_changes = self._getDOMPropertyChanges(baseline, actual)
        scr_changes = self._getScreenshotBasedChanges(baseline, actual)
        return dom_changes + scr_changes

    def _getDOMPropertyChanges(self, baseline, actual):
        ignored_keys = {"resource-id", "bounds", "index", "package"}
        changes = []

        for key in baseline.properties:
            if key not in ignored_keys and baseline.properties[key] != actual.properties.get(key):
                changes.append({
                    "Property": key.replace('-', ' ').title(),
                    "Baseline Value": baseline.properties[key],
                    "Actual Value": actual.properties.get(key)
                })

        return changes

    def _getScreenshotBasedChanges(self, baseline, actual):
        changes = []
        baseline_scr = Screenshot(self.baseline["screenshot"].image, baseline.bounds)
        actual_scr = Screenshot(self.actual["screenshot"].image, actual.bounds)

        baseline_props = baseline_scr.getProperties()
        actual_props = actual_scr.getProperties()

        # Check for image content differences
        if "image" in baseline.properties["class"].lower():
            if not ImageComparison(
                baseline_scr.cropped_image,
                actual_scr.cropped_image.resize(baseline_scr.cropped_image.size)
            ).areSame():
                changes.append({"Property": "Image", "Baseline Value": None, "Actual Value": None})

        # Check for text style differences if not caught in DOM
        if baseline.properties["text"] and actual.properties["text"] and baseline.properties["text"]==actual.properties["text"]:
            if (baseline_scr.getTextPixels() != actual_scr.getTextPixels()): #or (baseline_props["Text"] != actual_props.get("Text")):
                changes.append({"Property": "Text Style", "Baseline Value": None, "Actual Value": None})

        for key in baseline_props:
          if baseline_props[key] != actual_props.get(key):
            changes.append({
                "Property": key,
                "Baseline Value": baseline_props[key],
                "Actual Value": actual_props[key]
            })

        return changes

    def _addTip(self, zone, baseline_component, actual_component, label, old_value=None, new_value=None):
        description = self._getDescription(label, baseline_component, actual_component, old_value, new_value)

        # Check for duplicates
        for tip in self.tips:
            if tip["UI Component on Baseline"] == baseline_component and tip["UI Component on Actual"] == actual_component:
                if not any(d['Label'] == label for d in tip["Differences"]):
                    tip["Differences"].append({"Label": label, "Description": description})
                return

        # Determine resource-id
        resource_id = self._resolveResourceId(baseline_component, actual_component)
        self.tips.append({
            "Resource-id": resource_id or "No resource-id value found.",
            "UI Component on Baseline": baseline_component,
            "UI Component on Actual": actual_component,
            "Difference bounds": zone,
            "Differences": [{"Label": label, "Description": description}]
        })

    def _getDescription(self, label, baseline, actual, old_value, new_value):
        match label:
            case "UI Component missing":
                return f"UI Component {baseline} is missing."
            case "UI Component added":
                return f"UI Component {actual} was added."
            case "Colors changed":
                missing = set(old_value-new_value)
                added = set(new_value-old_value)
                if missing:
                    missing_text=f" Colors {missing} are missing."
                else:
                    missing_text=""
                if added:
                    added_text=f" Colors {added} were introduced."
                else:
                    added_text=""
                return (
                    f"The colors have changed.{missing_text}{added_text}"
                )
            case "Shape changed":
                return (
                    f"The geometric shape of the UI Component is not the same as previous. "
                    "Please verify the shape and theme definitions that may have affected the geometric shape of the content."
                )
            case "Text Style changed":
                return (
                    f"The text style is not the same as previous. "
                    "Please verify the text style changes that may have affected the appearence of the content."
                )
            case "Image changed":
                return (
                    f"The image asset is not the same as previous. "
                    "Please verify the image asset currently associated to its UI Component."
                )
            case _ if label.endswith("changed") and label not in {"Text Style changed", "Image changed", "Shape changed, Colors changed"}:
                prop = label.removesuffix(" changed")
                return f"{prop} has changed from '{old_value}' to '{new_value}'"
            case _:
                return "The system could not solve the difference. Please verify it manually."

    def _resolveResourceId(self, baseline, actual):
        if actual == "Unrelated":
            return baseline.properties.get('resource-id')
        if baseline == "Unrelated":
            return actual.properties.get('resource-id')
        if baseline.properties.get('resource-id') == actual.properties.get('resource-id'):
            return baseline.properties.get('resource-id')
        return f"Seems resource-id has being changed from {baseline.properties.get('resource-id')} to {actual.properties.get('resource-id')}"