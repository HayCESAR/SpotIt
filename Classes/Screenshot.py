import image_processing

class Screenshot:
    def __init__(self, image, bounds, children=None):
        self.image = self._highlight_box(image, bounds)
        self.image_without_children = self._remove_children(children)
        self.cropped_image = self._crop_image(image, bounds)
        self.colors = self._extract_colors(bounds)
        self.position = self._calculate_center(bounds)
        self.size = self._calculate_size(bounds)
        self.shape = self._detect_shape()
        self.text = self._extract_text()

    def _highlight_box(self, image, bounds):  
        # Highlights the bounding box of the component in the image
        return image_processing.addHighlight(image, [bounds])
    
    def _crop_image(self, image, bounds):  
        # Crops the image to the region defined by bounds
        return image_processing.cropImage(image, bounds)

    def _remove_children(self, children):  
        # Masks the image by excluding the areas covered by child components
        if not children:
            return self.image
        else:
            children_bounds = [child.bounds for child in children]
            return image_processing.addMask(self.image, children_bounds)

    def _extract_colors(self, bounds):  
        # Extracts the set of dominant colors from the cropped image region
        cropped = self.image.crop(bounds)
        return image_processing.getColorsFromImage(cropped)

    def _calculate_center(self, bounds):  
        # Calculates the center point of the bounding box
        x1, y1, x2, y2 = bounds
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _calculate_size(self, bounds):  
        # Computes the width and height from the bounding box
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        return (width, height)

    def _detect_shape(self):  
        # Identifies the visual shape of the component within its bounds
        return image_processing.getImageContentShape(self.image)

    def _extract_text(self):  
        # Extracts any text content from the image (excluding child areas)
        return image_processing.getTextFromImage(self.image_without_children)

    def getTextPixels(self):  
        # Returns the list of pixel coordinates corresponding to text regions
        return image_processing.listTextPixelsFromImage(self.image_without_children) 

    def getProperties(self):  
        # Returns a dict of the Screenshot's extracted properties
        return {
            "Colors": self.colors,
            "Position": self.position,
            "Size": self.size,
            "Shape": self.shape
        }
