import xml.dom.minidom
from Classes.UIComponent import UIComponent
import utils
from PyQt5.QtXml import QDomDocument
from PyQt5.QtCore import QFile, QIODevice

class UIHierarchy:
    def __init__(self, file_path):
        """Parses the XML file and builds a hierarchy of UIComponent objects."""
        self.file_path = file_path
        self.root_component = self._parse_xml_to_objects()

    def _parse_xml_to_objects(self):
        """Reads and formats the XML before parsing to ensure correct line numbers."""
        # Read the raw XML
        with open(self.file_path, "r", encoding="utf-8") as file:
            raw_xml = file.read()

        # Check if the XML is a single-line document (no newline characters)
        if "\n" not in raw_xml.strip():
            print("\tDetected single-line XML, applying pretty-printing...")
            raw_xml = self._pretty_format_xml(raw_xml)

        # Save formatted XML back to a temporary file for parsing
        temp_file_path = f"output/temp_formatted_{self.file_path.split('/')[-1]}.xml"
        with open(temp_file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(raw_xml)

        # Open and parse the formatted XML file
        file = QFile(temp_file_path)
        if not file.open(QIODevice.ReadOnly | QIODevice.Text):
            raise FileNotFoundError(f"Failed to open file: {temp_file_path}")

        doc = QDomDocument()
        if not doc.setContent(file):
            file.close()
            raise ValueError("Failed to parse XML.")

        file.close()

        # Recursively build the component tree
        root_element = doc.documentElement()
        return self._build_component_tree(root_element, None)

    def _pretty_format_xml(self, xml_str):
        """Formats the XML string into a readable, multi-line format."""
        dom = xml.dom.minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")

    def _build_component_tree(self, element, parent_component):
        """Recursively builds a tree of UIComponent objects."""
        if element.isNull():
            return None

        # Get element name, line number, and attributes
        element_name = element.tagName()
        line_number = element.lineNumber()
        properties = self._get_attributes_dict(element)

        # Create UIComponent object
        component = UIComponent(element_name, line_number, properties, parent_component)

        # Add to parent's children if a parent exists
        if parent_component:
            parent_component.add_child(component)

        # Process child elements
        child = element.firstChild()
        while not child.isNull():
            child_element = child.toElement()
            if not child_element.isNull():
                self._build_component_tree(child_element, component)
            child = child.nextSibling()

        return component if not parent_component else None  # Return root component

    def _get_attributes_dict(self, element):
        """Returns a dictionary of element attributes."""
        attributes = {}
        attr_map = element.attributes()
        for i in range(attr_map.count()):
            attr = attr_map.item(i).toAttr()
            attributes[attr.name()] = attr.value()
        return attributes

    def list_all_components(self):
        """Returns a list of all UIComponent objects in the hierarchy."""
        all_components = []
        self._collect_components(self.root_component, all_components)
        return all_components

    def _collect_components(self, component, all_components):
        """Recursively collects all components into a list."""
        if component:
            all_components.append(component)
            for child in component.children:
                self._collect_components(child, all_components)

    def get_document_dimensions(self):
        """Calculates the total UI document dimensions based on the largest x2, y2 found."""
        max_x, max_y = self._calculate_document_dimensions(self.root_component)
        return max_x, max_y

    def _calculate_document_dimensions(self, component):
        """Recursively finds the maximum x2 and y2 values in all bounds."""
        max_x, max_y = 0, 0

        if component:
            bounds = component.properties.get("bounds")
            if bounds:
                try:
                    _, _, x2, y2 = utils.parse_bounds_str(bounds)
                    max_x = max(max_x, x2)
                    max_y = max(max_y, y2)
                except ValueError:
                    pass  # Ignore invalid bounds

            for child in component.children:
                child_max_x, child_max_y = self._calculate_document_dimensions(child)
                max_x = max(max_x, child_max_x)
                max_y = max(max_y, child_max_y)

        return max_x, max_y  # Return the actual maximum dimensions

    def get_bounds_excluding_package(self, package_name):
        """Returns the bounds of all components that do NOT belong to the specified package."""
        excluded_bounds = []
        self._collect_bounds_excluding_package(self.root_component, package_name, excluded_bounds)
        return excluded_bounds

    def _collect_bounds_excluding_package(self, component, package_name, excluded_bounds):
        """Recursively collects bounds of components not matching the specified package."""
        if component:
            component_package = component.properties.get("package")
            if component_package != package_name:  # Exclude components in this package
                bounds = component.properties.get("bounds")
                if bounds:
                    excluded_bounds.append((component, utils.parse_bounds_str(bounds)))

            for child in component.children:
                self._collect_bounds_excluding_package(child, package_name, excluded_bounds)

    def find_component_by_line(self, target_line):
        """Finds a UIComponent by its line number."""
        return self._find_component_by_line(self.root_component, target_line)

    def _find_component_by_line(self, component, target_line):
        """Recursively searches for a UIComponent with the given line number."""
        if component.sourceLine == target_line:
            return component

        for child in component.children:
            result = self._find_component_by_line(child, target_line)
            if result:
                return result

        return None

    def find_components_containing_bounds(self, boundbox):
        """
        Recursively verifies from the root to the children which components contain the given bounding box.
        Ensures that if a parent contains the bounds, all its children are also verified.

        Returns a list of the smallest components that contain the bounding box.
        """
        return self._search_containing_components(self.root_component, boundbox[0], boundbox[1], boundbox[2], boundbox[3])

    def _search_containing_components(self, component, x, y, w, h):
        """
        Recursively finds all components containing the bounding box and ensures all matching children are also checked.
        """
        if not component:
            return []

        matching_components = []

        # If the current component contains the bounding box, check its children
        if component.bounds and utils.is_contained((x, y, x+w, y+h), component.bounds):
            children_matches = []

            # Check all children to see if they also contain the bounding box
            for child in component.children:
                child_results = self._search_containing_components(child, x, y, w, h)
                children_matches.extend(child_results)  # Collect all matching children

            # If children match, return them instead of the parent
            if children_matches:
                return children_matches + matching_components  # Return all children matches

            # If no children matched, return the parent
            matching_components.append(component)

        # If the current component doesn't match, continue searching in its children
        for child in component.children:
            matching_components.extend(self._search_containing_components(child, x, y, w, h))

        return matching_components  # Return all collected matches
