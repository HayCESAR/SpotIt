import cv2
import numpy as np
import image_processing
import pytesseract
import matplotlib.pyplot as plt

class Screenshot:
    def __init__(self, image, bounds, children=None):
        self.image = image_processing.addHighlight(image, [bounds])
        self.image_without_children = self._removeChildren(children)
        self.colors = self._extract_colors(bounds)
        self.position = self._calculate_center(bounds)
        self.size = self._calculate_size(bounds)
        self.shape = self._detect_shape()
        self.text = self._extract_text()

    def _removeChildren(self, children):
        if not children:
            return self.image
        else:
            children_bounds = [child.bounds for child in children]
            return image_processing.addMask(self.image, children_bounds)

    def _extract_colors(self, bounds):
        cropped = self.image.crop(bounds)
        component = cropped.convert('RGB')
        min_percentage = 0.5  # min percentage of color in the image to be added

        all_pixels = component.size[0] * component.size[1]
        colors_hm = {}
        sorted_colors = []

        for rgba_pixel in component.getdata():
            # Count colors
            nb = colors_hm.get(rgba_pixel, {'nb': 0})['nb']
            colors_hm[rgba_pixel] = {'nb': nb + 1}

        # Collect color percentages
        for color in colors_hm:
            color_percentage = colors_hm[color]['nb'] * 100 / float(all_pixels)
            if color_percentage >= min_percentage:
                sorted_colors.append({'color': color, 'num': color_percentage})

        # Sort colors by percentage in descending order
        sorted_colors.sort(key=lambda k: k['num'], reverse=True)

        # Extract just the color values in the desired format (hex or RGB)
        color_array = []
        for x in sorted_colors:
            color_array.append((x['color'][0], x['color'][1], x['color'][2]))

        # Print the result
        return(set(color_array))

    def _calculate_center(self, bounds):
        x1, y1, x2, y2 = bounds
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _calculate_size(self, bounds):
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        return (width, height)

    def _detect_shape(self):
        img = np.array(self.image)
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply a Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # Use Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return(len(contours[0]))

    def _extract_text(self):
        return pytesseract.image_to_string(self.image).strip().replace('\n', ' ')

    def removeChildren(self, children_bounds):
        return image_processing.addMask(self.image, children_bounds)

    def show_image(self):
        plt.imshow(self.image)
        plt.axis('off')
        plt.show()

    def getProperties(self):
        """Returns a dict representation of the Screenshot."""
        return {"Colors": self.colors, "Position": self.position, "Size": self.size, "Shape": self.shape, "Text": self.text}
