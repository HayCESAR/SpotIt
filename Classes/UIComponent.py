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
        # Parses the bounds property and convert it to the format (x1, y1, x2, y2)
        if "bounds" in self.properties:
            return utils.parse_bounds_str(self.properties["bounds"])
        else:
            return None

    def addCorrelation(self, correlation):
        # Adds the corresponding component from the other source (baseline/actual)
        self.correlation = correlation

    def addScreenshot(self, image):
        # Adds image representation for this component
        if self.bounds:
            self.screenshot = Screenshot(image, self.bounds, self.children)

    def add_child(self, child):
        # Adds a child UIComponent to this component
        self.children.append(child)

    def getStates(self):
        # Gets states as: focused, checked, scrollable, enabled, etc...
        exclude_keys = {"resource-id", "class", "content-desc", "text"}
        return {
            key: value
            for key, value in self.properties.items()
            if key not in exclude_keys
        }

    def as_dict(self):
        # Gets the main representative properties from the UI Component
        return {
          "line": self.sourceLine,
          "resource-id": self.properties.get("resource-id", "N/A"),
          "class": self.properties.get("class", "N/A"),
          "content-desc": self.properties.get("content-desc", "N/A"),
          "text": self.properties.get("text", "N/A"),
          "bounds": self.bounds
        }

    def __eq__(self, other):
        # Defines how UIComponents objects are compared for equalness validation
        if isinstance(other, UIComponent):
            return self.elementName == other.elementName and self.properties == other.properties
        return False

    def __repr__(self):
        # Defines a string representation of the UIComponent
        return f"UIComponent(Name: {self.elementName}, Line: {self.sourceLine}, Properties: {self.properties})"