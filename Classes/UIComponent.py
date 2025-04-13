from Classes.Screenshot import Screenshot
import utils

class UIComponent:
    def __init__(self, elementName, sourceLine, properties, parent=None):
        self.elementName = elementName  # XML element name (tag)
        self.sourceLine = sourceLine  # Line number in XML
        self.properties = properties  # Dictionary of attributes
        self.parent = parent  # Reference to parent UIComponent
        self.children = []  # List of child UIComponents
        self.bounds = self._get_bounds()
        self.screenshot = None
        self.correlation = None

    def _get_bounds(self):
        if "bounds" in self.properties:
            return utils.parse_bounds_str(self.properties["bounds"])
        else:
            return None

    def addCorrelation(self, correlation):
        self.correlation = correlation

    def addScreenshot(self, image):
        if self.bounds:
            self.screenshot = Screenshot(image, self.bounds, self.children)

    def add_child(self, child):
        """Adds a child UIComponent to this component."""
        self.children.append(child)

    def as_dict(self):
        return {
          "line": self.sourceLine,
          "resource-id": self.properties.get("resource-id", "N/A"),
          "class": self.properties.get("class", "N/A"),
          "content-desc": self.properties.get("content-desc", "N/A"),
          "text": self.properties.get("text", "N/A"),
          "bounds": self.bounds
        }

    def __eq__(self, other):
        if isinstance(other, UIComponent):
            return self.elementName == other.elementName and self.properties == other.properties
        return False

    def __repr__(self):
        """Returns a string representation of the UIComponent."""
        return f"UIComponent(Name: {self.elementName}, Line: {self.sourceLine}, Properties: {self.properties})"