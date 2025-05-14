from Classes.UIHierarchy import UIHierarchy
from Classes.Screenshot import Screenshot
from Classes.Oracle import Oracle
from Classes.Comparators.ImageComparison import ImageComparison
from Classes.Comparators.UIComponentsComparison import UIComponentsComparison
from PIL import Image
import cv2
import image_processing
import sys

def setUIHierarchy(filepath, package):
    dom = UIHierarchy(filepath)
    return dom, dom.get_document_dimensions(), dom.get_bounds_excluding_package(package)

def setScreenshot(filepath, dimension, excluded_bounds):
    image = Image.open(filepath)
    width, height = dimension
    bounds_array = [(bounds[0], bounds[1], bounds[2], bounds[3]) for _, bounds in excluded_bounds]
    app_screen = image_processing.addMask(image, bounds_array)
    if image_processing.is_image_all_black(app_screen):
        print('No package components detected.')
        return None
    else:
        scr = Screenshot(app_screen, (0,0, width, height))
    return scr

def getUIComponentsInDifferenceZones(baseline, actual, boundboxes):
    # Verify the visual change is really contained in this component rendering
    def verifyByImage(uicomponent):
        change_found = []
        children_bounds = []
        if uicomponent.correlation:
            if uicomponent.children:
                children_bounds.extend([child.bounds for child in uicomponent.children])
            if uicomponent.correlation['UIComponent'].children:
                children_bounds.extend([child.bounds for child in uicomponent.correlation['UIComponent'].children])
            uicomponent_without_children = image_processing.addMask(uicomponent.screenshot.image, children_bounds)
            related_uicomponent_without_children = image_processing.addMask(uicomponent.correlation['UIComponent'].screenshot.image, children_bounds)
            comparison_uicomponents_visual = ImageComparison(uicomponent_without_children, related_uicomponent_without_children)

            if comparison_uicomponents_visual.areSame():
                if not uicomponent.children:
                    return []
                else:
                    for child in uicomponent.children:
                        result = verifyByImage(child)
                        if result:
                            if isinstance(result, list):
                                change_found.extend(result)
                            else:
                                change_found.append(result)
                return change_found
            else:
                return [uicomponent]
        else:
            return [uicomponent]
    
    uicomponents_in_difference_zone = {}

    # Getting the UIComponents that contain each difference zone for both sources
    for bound_box in boundboxes:
        new_area = {str(bound_box): {"baseline": baseline['uihierarchy'].find_components_containing_bounds(bound_box), "actual": actual['uihierarchy'].find_components_containing_bounds(bound_box)}}

        # Verify if an UIComponents should be replaced by its child
        for source in new_area[str(bound_box)]:
            to_extend=[]
            to_remove=[]
            for uicomponent in new_area[str(bound_box)][source]:
                verified_uicomponent = verifyByImage(uicomponent)
            if [uicomponent]!=verified_uicomponent:
                to_extend.extend(verified_uicomponent)
                to_remove.append(uicomponent)
            new_area[str(bound_box)][source].extend(to_extend)
            new_area[str(bound_box)][source] = [item for item in new_area[str(bound_box)][source] if item not in to_remove]

        # Join the difference zones with same affected UIComponents
        repeated=False
        for key in uicomponents_in_difference_zone:
            if new_area[str(bound_box)]==uicomponents_in_difference_zone[key]:
                uicomponents_in_difference_zone[key+','+str(bound_box)] = uicomponents_in_difference_zone.pop(key)
                repeated=True
                break
        if not repeated:
            uicomponents_in_difference_zone.update(new_area)
            
    return uicomponents_in_difference_zone

baseline_png = sys.argv[1]
baseline_xml = sys.argv[2]
actual_png = sys.argv[3]
actual_xml = sys.argv[4]
app_package = sys.argv[5]
output = sys.argv[6]

#Defining Baseline
print("Getting baseline data...")
baseline_uihierarchy, baseline_dimension, baseline_excluded_bounds = setUIHierarchy(baseline_xml, app_package)
if baseline_uihierarchy:
    print("\tUIHierarchy: ok")
    print(f"\tScreen dimension: {baseline_dimension}")
    print(f"\tNo package matching bounds: {baseline_excluded_bounds}")
baseline_screenshot = setScreenshot(baseline_png, baseline_dimension, baseline_excluded_bounds)
if baseline_screenshot:
    print("Baseline Screenshot: OK")

#Defining Actual
print("Getting actual data...")
actual_uihierarchy, actual_dimension, actual_excluded_bounds = setUIHierarchy(actual_xml, app_package)
if actual_uihierarchy:
    print("\tUIHierarchy: ok")
    print(f"\tScreen dimension: {actual_dimension}")
    print(f"\tNo package matching bounds: {actual_excluded_bounds}")
actual_screenshot = setScreenshot(actual_png, actual_dimension, actual_excluded_bounds)
if actual_screenshot:
    print("Actual Screenshot: OK")

#Compare screenshots
print("\nComparing screenshots...")
comparison_scr = ImageComparison(baseline_screenshot.image, actual_screenshot.image)

# If differences are detected
if not comparison_scr.areSame():
    # Save the visual reports of the differences
    cv2.imwrite(f'{output}/diff_output.png', comparison_scr.diff)
    cv2.imwrite(f'{output}/baseline_with_boxes.png', comparison_scr.spoted_on_baseline)
    cv2.imwrite(f'{output}/actual_with_boxes.png', comparison_scr.spoted_on_actual)
    print(f"Differences have been saved into output folder.")

    # Identify the related components
    comparison_uicomponents = UIComponentsComparison(baseline_uihierarchy, actual_uihierarchy)

    # Get isoleted images for each UI component
    baseline_uicomponents = baseline_uihierarchy.list_all_components()
    actual_uicomponents = actual_uihierarchy.list_all_components()
    for uicomponent in baseline_uicomponents:
        uicomponent.addScreenshot(baseline_screenshot.image)
    for uicomponent in actual_uicomponents:
        uicomponent.addScreenshot(actual_screenshot.image)

    # Identify the affected components
    uicomponents_in_difference_zones = getUIComponentsInDifferenceZones({'uihierarchy': baseline_uihierarchy, 'screenshot': baseline_screenshot}, {'uihierarchy': actual_uihierarchy, 'screenshot': actual_screenshot}, comparison_scr.boundboxes)

    # Write the textual reports with changes classifications
    oracle = Oracle({"screenshot": baseline_screenshot, "uihierarchy": baseline_uihierarchy}, {"screenshot": actual_screenshot, "uihierarchy": actual_uihierarchy}, uicomponents_in_difference_zones)
    tips=oracle.getTips()
    for tip in tips:
        print(f"\nResource-id: {tip['Resource-id']}\nUI Component on Baseline: {tip['UI Component on Baseline']}\nUI Component on Actual: {tip['UI Component on Actual']}\nDifference bounds: {tip['Difference bounds']}\nDifferences: {tip['Differences']}")

# If no differences are detected
else:
  print("PASSED. No differences found.")