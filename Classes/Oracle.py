from Classes.Screenshot import Screenshot

class Oracle:
  def __init__(self, baseline, actual, uicomponents_in_difference_zones):
    self.baseline = baseline
    self.actual = actual
    self.uicomponents_in_difference_zones = uicomponents_in_difference_zones
    self.tips = []

  def _identifyChanges(self, key, component):
    changes = self._compareProperties(component, component.correlation["UIComponent"])
    for change in changes:
      self._addTip(key, component, component.correlation["UIComponent"], f"{change['Property']} changed", change['Baseline Value'], change['Actual Value'])

  def _compareProperties(self, baseline, actual):
    ignored_keys=["resource-id", "bounds", "index", "package"]
    dom_changes=[]
    if baseline != actual:
      for key in baseline.properties:
        if not key in ignored_keys and baseline.properties[key]!=actual.properties[key]:
          dom_changes.append({"Property": key.replace('-', ' ').title(), "Baseline Value": baseline.properties[key], "Actual Value": actual.properties[key]})
    #baseline_uicomponent_scr = Screenshot(self.baseline["screenshot"].image, (288, 857, 900, 1041)) #CHANGE HERE
    baseline_uicomponent_scr = Screenshot(self.baseline["screenshot"].image, baseline.bounds)
    #actual_uicomponent_scr = Screenshot(self.actual["screenshot"].image, (288, 857, 900, 1041)) #CHANGE HERE
    actual_uicomponent_scr = Screenshot(self.actual["screenshot"].image, actual.bounds)
    baseline_scr_properties = baseline_uicomponent_scr.getProperties()
    actual_scr_properties = actual_uicomponent_scr.getProperties()
    scr_changes=[]
    for key in baseline_scr_properties:
      if baseline_scr_properties[key]!=actual_scr_properties[key]:
        if key=="Text":
          if not any(change.get("Property")=="Text" for change in dom_changes):
            scr_changes.append({"Property": "Text Style", "Baseline Value": baseline_scr_properties[key], "Actual Value": actual_scr_properties[key]})
        else:
          scr_changes.append({"Property": key, "Baseline Value": baseline_scr_properties[key], "Actual Value": actual_scr_properties[key]})
    changes = dom_changes+scr_changes
    return changes

  def _addTip(self, difference_zone, uicomponent_baseline, uicomponent_actual, label, old_value=None, new_value=None):
    match label:
      case "UI Component missing":
        description = f"UI Component {uicomponent_baseline} is missing."
      case "UI Component added":
        description = f"UI Component {uicomponent_actual} was added."
      case "Text Style changed":
        description = f"The visible text changed from '{old_value}''to '{new_value}'. Please verify the text style changes that may have affected the visibility of the content.'"
      case "Shape changed":
        description=f"Shape has changed from {old_value} edges detected to {new_value} edges detected."
      case s if s.endswith('changed') and s!="Text Style" and s!="Shape changed":
        description = f"{s.removesuffix(' changed')} has changed from '{old_value}' to '{new_value}'"
      case _:
        description = f"The system could not solve the difference. Please verify it manually."

    already_exists=False
    for tip in self.tips:
      if tip["UI Component on Baseline"]==uicomponent_baseline and tip["UI Component on Actual"]==uicomponent_actual:
        tip["Differences"].append({"Label": label, "Description": description})
        already_exists=True
        break
    if not already_exists:
      if uicomponent_baseline.properties['resource-id']==uicomponent_actual.properties['resource-id'] or uicomponent_actual=="Unrelated":
        resource_id = uicomponent_baseline.properties['resource-id']
      elif uicomponent_baseline.properties['resource-id']=="Unrelated":
        resource_id = uicomponent_actual.properties['resource-id']
      else:
        resource_id = f"Seems resource-id has being changed from {uicomponent_baseline.properties['resource-id']} to {uicomponent_actual.properties['resource-id']}"
      self.tips.append({"Resource-id": resource_id if resource_id else "No resource-id value found for these components.", "UI Component on Baseline": uicomponent_baseline, "UI Component on Actual": uicomponent_actual, "Difference bounds": difference_zone, "Differences": [{"Label": label, "Description": description}]})
      return self.tips

  def getTips(self):
    wanted_missing=[]
    wanted_added=[]
    for key in self.uicomponents_in_difference_zones:
      for component in self.uicomponents_in_difference_zones[key]['baseline']:
        if component:
          if component.correlation["UIComponent"]=="Unrelated":
            self._addTip(key, component, "Unrelated", "UI Component missing")
          elif component.correlation["UIComponent"] not in self.uicomponents_in_difference_zones[key]['actual']:
            if component in wanted_added:
              wanted_added.remove(component)
              self._identifyChanges(key, component)
            else:
              wanted_missing.append(component.correlation["UIComponent"])
          else:
            self._identifyChanges(key, component)
      for component in self.uicomponents_in_difference_zones[key]['actual']:
        if component:
          if component.correlation["UIComponent"]=="Unrelated":
            self._addTip(key, "Unrelated", component, "UI Component added")
          elif component.correlation["UIComponent"] not in self.uicomponents_in_difference_zones[key]['baseline']:
            if component in wanted_missing:
              wanted_missing.remove(component)
              self._identifyChanges(key, component.correlation["UIComponent"])
            else:
              wanted_added.append(component.correlation["UIComponent"])

    return self.tips
