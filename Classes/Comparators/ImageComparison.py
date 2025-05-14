import cv2
import numpy as np

class ImageComparison:
    def __init__(self, baseline_image, actual_image):
        # Store the baseline and actual images (as PIL Images)
        self.baseline = baseline_image
        self.actual = actual_image
        self.diff = None  # Will store the grayscale difference image
        self.boundboxes = None  # Will store bounding boxes around detected differences
        self.spoted_on_actual = None  # Actual image with difference boxes drawn
        self.spoted_on_baseline = None  # Baseline image with difference boxes drawn

    def areSame(self):
        """
        Compares the baseline and actual images.
        Returns True if no visual differences are detected, False otherwise.
        """
        # Convert PIL images to NumPy arrays (OpenCV compatible)
        baseline_image_np = np.array(self.baseline)
        actual_image_np = np.array(self.actual)

        # Generate difference data and visualizations
        self.diff, self.boundboxes, self.spoted_on_actual, self.spoted_on_baseline = self._getDiffImage(
            baseline_image_np, actual_image_np
        )

        # Return True only if no bounding boxes (i.e., no visual changes)
        return not self.boundboxes

    def _getDiffImage(self, baseline_image_np, actual_image_np):
        """
        Performs pixel-by-pixel image comparison using OpenCV.
        Returns:
        - grayscale diff image,
        - bounding boxes around visual differences,
        - annotated actual image,
        - annotated baseline image.
        """
        # Ensures the images have the same dimensions before comparison
        if baseline_image_np.shape != actual_image_np.shape:
            raise ValueError("Images must have the same dimensions for pixel-by-pixel comparison")

        # Computes absolute difference between images
        diff = cv2.absdiff(baseline_image_np, actual_image_np)

        # Converts to grayscale to simplify processing
        diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Applies threshold to emphasize significant pixel differences
        _, thresholded = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

        # Finds contours of the differences (connected components)
        contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Computes bounding boxes around each detected difference contour
        bounding_boxes = [cv2.boundingRect(contour) for contour in contours]

        # Prepares annotated versions of both images (convert to BGR for drawing in OpenCV)
        baseline_with_boxes = cv2.cvtColor(baseline_image_np, cv2.COLOR_RGB2BGR)
        actual_with_boxes = cv2.cvtColor(actual_image_np, cv2.COLOR_RGB2BGR)

        # Draw red rectangles (boxes) around the differences on both images
        for box in bounding_boxes:
            x, y, w, h = box
            cv2.rectangle(actual_with_boxes, (int(x), int(y)), (int(x) + int(w), int(y) + int(h)), (0, 0, 255), 2)
            cv2.rectangle(baseline_with_boxes, (int(x), int(y)), (int(x) + int(w), int(y) + int(h)), (0, 0, 255), 2)

        # Returns the diff image, list of bounding boxes, and both annotated images
        return diff, bounding_boxes, actual_with_boxes, baseline_with_boxes
