from Classes.UIHierarchy import UIHierarchy
from Classes.Screenshot import Screenshot
from Classes.Oracle import Oracle
from Classes.Comparators.ImageComparison import ImageComparison
from Classes.Comparators.UIComponentsComparison import UIComponentsComparison
from PIL import Image
import cv2
import image_processing

def setUIHierarchy(filepath, package):
    dom = UIHierarchy(filepath)
    return dom, dom.get_document_dimensions(), dom.get_bounds_excluding_package(package)

def setScreenshot(filepath, dimension, excluded_bounds):
    def is_image_all_black(img):
        """Check if a given PIL image is entirely black."""
        # Convert image to grayscale
        grayscale_img = img.convert("L")
        # Get all pixel values
        pixels = grayscale_img.getdata()
        # Check if all pixels are black (0)
        return all(pixel == 0 for pixel in pixels)

    image = Image.open(filepath)
    width, height = dimension
    bounds_array = [(bounds[0], bounds[1], bounds[2], bounds[3]) for _, bounds in excluded_bounds]
    app_screen = image_processing.addMask(image, bounds_array)
    if is_image_all_black(app_screen):
        print('No package components detected.')
        return None
    else:
        scr = Screenshot(app_screen, (0,0, width, height))
    return scr

def getUIComponentsInDifferenceZones(baseline, actual, boundboxes):
    def verifyByImage(uicomponent):
        children_bounds = []
        if uicomponent.children:
            children_bounds.extend([child.bounds for child in uicomponent.children])
        if uicomponent.correlation['UIComponent'].children:
            children_bounds.extend([child.bounds for child in uicomponent.correlation['UIComponent'].children])
        uicomponent_without_children = image_processing.addMask(uicomponent.screenshot.image, children_bounds)
        related_uicomponent_without_children = image_processing.addMask(uicomponent.correlation['UIComponent'].screenshot.image, children_bounds)
        comparison_uicomponents_visual = ImageComparison(uicomponent_without_children, related_uicomponent_without_children)
        if comparison_uicomponents_visual.areSame():
            if not uicomponent.children:
                return None
            else:
                for child in uicomponent.children:
                    result = verifyByImage(child)
                    if result:
                        return result
        else:
            return uicomponent
    
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
            if uicomponent!=verified_uicomponent:
                #print(f"\tLet's change {uicomponent.sourceLine} for {verified_uicomponent.sourceLine}")
                to_extend.append(verified_uicomponent)
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

app_package = "com.example.hellofigma"

#Defining Baseline
print("Getting baseline data...")
baseline_uihierarchy, baseline_dimension, baseline_excluded_bounds = setUIHierarchy("samples/baseline/UIHierarchy_baseline_button.xml", app_package)
if baseline_uihierarchy:
    print("\tUIHierarchy: ok")
    print(f"\tScreen dimension: {baseline_dimension}")
    print(f"\tNo package matching bounds: {baseline_excluded_bounds}")
baseline_screenshot = setScreenshot("samples/baseline/screenshot_baseline_button.png", baseline_dimension, baseline_excluded_bounds)
if baseline_screenshot:
    baseline_screenshot.show_image()

#Defining Actual
print("Getting actual data...")
actual_uihierarchy, actual_dimension, actual_excluded_bounds = setUIHierarchy("samples/position_button/UIHierarchy_actual_button.xml", app_package)
if actual_uihierarchy:
    print("\tUIHierarchy: ok")
    print(f"\tScreen dimension: {actual_dimension}")
    print(f"\tNo package matching bounds: {actual_excluded_bounds}")
actual_screenshot = setScreenshot("samples/position_button/screenshot_actual_button.png", actual_dimension, actual_excluded_bounds)
if actual_screenshot:
    actual_screenshot.show_image()

#Compare screenshots
print("\nComparing screenshots...")
comparison_scr = ImageComparison(baseline_screenshot.image, actual_screenshot.image)
if not comparison_scr.areSame():
    cv2.imwrite('output/diff_output.png', comparison_scr.diff)
    cv2.imwrite('output/baseline_with_boxes.png', comparison_scr.spoted_on_baseline)
    cv2.imwrite('output/actual_with_boxes.png', comparison_scr.spoted_on_actual)
    print(f"Differences have been saved into output folder.")

    comparison_uicomponents = UIComponentsComparison(baseline_uihierarchy, actual_uihierarchy)

    baseline_uicomponents = baseline_uihierarchy.list_all_components()
    actual_uicomponents = actual_uihierarchy.list_all_components()
    for uicomponent in baseline_uicomponents:
        uicomponent.addScreenshot(baseline_screenshot.image)
    for uicomponent in actual_uicomponents:
        uicomponent.addScreenshot(actual_screenshot.image)

    uicomponents_in_difference_zones = getUIComponentsInDifferenceZones({'uihierarchy': baseline_uihierarchy, 'screenshot': baseline_screenshot}, {'uihierarchy': actual_uihierarchy, 'screenshot': actual_screenshot}, comparison_scr.boundboxes)

    oracle = Oracle({"screenshot": baseline_screenshot, "uihierarchy": baseline_uihierarchy}, {"screenshot": actual_screenshot, "uihierarchy": actual_uihierarchy}, uicomponents_in_difference_zones)
    tips=oracle.getTips()
    for tip in tips:
        print()
        print()
        print()
        print(f"Resource-id: {tip['Resource-id']}\nUI Component on Baseline: {tip['UI Component on Baseline']}\nUI Component on Actual: {tip['UI Component on Actual']}\nDifference bounds: {tip['Difference bounds']}\nDifferences: {tip['Differences']}")

else:
  print("PASSED. No differences found.")