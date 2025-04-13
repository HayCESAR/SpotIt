from PIL import ImageChops, ImageDraw
import cv2
import numpy as np

class ImageComparison:
    def __init__(self, baseline_image, actual_image):
        self.baseline = baseline_image
        self.actual = actual_image
        self.diff = None
        self.boundboxes = None
        self.spoted_on_actual = None
        self.spoted_on_baseline = None

    def areSame(self):
        baseline_image_np = np.array(self.baseline)
        actual_image_np = np.array(self.actual)
        self.diff, self.boundboxes, self.spoted_on_actual, self.spoted_on_baseline = self._getDiffImage(baseline_image_np, actual_image_np)
        if not self.boundboxes:
            return True
        else:
            return False

    def _getDiffImage(self, baseline_image_np, actual_image_np):
        # Make sure the images are the same size
        if baseline_image_np.shape != actual_image_np.shape:
            raise ValueError("Images must have the same dimensions for pixel-by-pixel comparison")

        diff = cv2.absdiff(baseline_image_np, actual_image_np)
        diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, thresholded = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bounding_boxes = [cv2.boundingRect(contour) for contour in contours]

        baseline_with_boxes = cv2.cvtColor(baseline_image_np, cv2.COLOR_RGB2BGR)
        actual_with_boxes = cv2.cvtColor(actual_image_np, cv2.COLOR_RGB2BGR)
        for box in bounding_boxes:
            x, y, w, h = box
            cv2.rectangle(actual_with_boxes, (int(x), int(y)), (int(x) + int(w), int(y) + int(h)), (0, 0, 255), 2)
            cv2.rectangle(baseline_with_boxes, (int(x), int(y)), (int(x) + int(w), int(y) + int(h)), (0, 0, 255), 2)

        return diff, bounding_boxes, actual_with_boxes, baseline_with_boxes