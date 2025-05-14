import xml.dom.minidom
from Classes.UIComponent import UIComponent
import utils
from PyQt5.QtXml import QDomDocument
from PyQt5.QtCore import QFile, QIODevice

class UIHierarchy:
    def __init__(self, file_path):
        # Initializes the UIHierarchy by parsing the given XML file and building a UI component tree.
        self.file_path = file_path
        self.root_component = self._parse_xml_to_objects()

    def _parse_xml_to_objects(self):
        """
        Parses the XML structure into a tree of UIComponent objects.
        Applies pretty formatting if the XML is a single line.
        :return: Root component of the hierarchy.
        """
        with open(self.file_path, "r", encoding="utf-8") as file:
            raw_xml = file.read()

        if "\n" not in raw_xml.strip():
            print("\tDetected single-line XML, applying pretty-printing...")
            raw_xml = self._pretty_format_xml(raw_xml)

        temp_file_path = f"output/temp_formatted_{self.file_path.split('/')[-1]}"
        with open(temp_file_path, "w", encoding="utf-8") as temp_file:
            temp_file.write(raw_xml)

        file = QFile(temp_file_path)
        if not file.open(QIODevice.ReadOnly | QIODevice.Text):
            raise FileNotFoundError(f"Failed to open file: {temp_file_path}")

        doc = QDomDocument()
        if not doc.setContent(file):
            file.close()
            raise ValueError("Failed to parse XML.")

        file.close()
        root_element = doc.documentElement()
        return self._build_component_tree(root_element, None)

    def _pretty_format_xml(self, xml_str):
        """
        Formats an XML string into indented, multi-line format.

        :param xml_str: Raw XML string.
        :return: Pretty-formatted XML string.
        """
        dom = xml.dom.minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")

    def _build_component_tree(self, element, parent_component):
        """
        Recursively builds a tree of UIComponent objects from QDom elements.

        :param element: Current XML element being processed.
        :param parent_component: Parent UIComponent object.
        :return: Root UIComponent (only at the top call).
        """
        if element.isNull():
            return None

        element_name = element.tagName()
        line_number = element.lineNumber()
        properties = self._get_attributes_dict(element)
        component = UIComponent(element_name, line_number, properties, parent_component)

        if parent_component:
            parent_component.add_child(component)

        child = element.firstChild()
        while not child.isNull():
            child_element = child.toElement()
            if not child_element.isNull():
                self._build_component_tree(child_element, component)
            child = child.nextSibling()

        return component if not parent_component else None

    def _get_attributes_dict(self, element):
        """
        Extracts attributes from a QDomElement into a dictionary.

        :param element: QDomElement with attributes.
        :return: Dictionary of attribute name-value pairs.
        """
        attributes = {}
        attr_map = element.attributes()
        for i in range(attr_map.count()):
            attr = attr_map.item(i).toAttr()
            attributes[attr.name()] = attr.value()
        return attributes

    def list_all_components(self):
        """
        Collects and returns a flat list of all UIComponent objects in the hierarchy.

        :return: List of UIComponent objects.
        """
        all_components = []
        self._collect_components(self.root_component, all_components)
        return all_components

    def _collect_components(self, component, all_components):
        """
        Recursively traverses the component tree and collects all components.

        :param component: Current component being traversed.
        :param all_components: List to store collected components.
        """
        if component:
            all_components.append(component)
            for child in component.children:
                self._collect_components(child, all_components)

    def get_document_dimensions(self):
        """
        Computes the maximum width and height of the UI based on the largest bounds.

        :return: Tuple (max_x, max_y) representing screen dimensions.
        """
        max_x, max_y = self._calculate_document_dimensions(self.root_component)
        return max_x, max_y

    def _calculate_document_dimensions(self, component):
        """
        Recursively finds the furthest (x2, y2) point across all bounds.

        :param component: Current UIComponent being analyzed.
        :return: Tuple (max_x, max_y) for this subtree.
        """
        max_x, max_y = 0, 0

        if component:
            bounds = component.properties.get("bounds")
            if bounds:
                try:
                    _, _, x2, y2 = utils.parse_bounds_str(bounds)
                    max_x = max(max_x, x2)
                    max_y = max(max_y, y2)
                except ValueError:
                    pass

            for child in component.children:
                child_max_x, child_max_y = self._calculate_document_dimensions(child)
                max_x = max(max_x, child_max_x)
                max_y = max(max_y, child_max_y)

        return max_x, max_y

    def get_bounds_excluding_package(self, package_name):
        """
        Retrieves bounds of components that do NOT match the given package name.

        :param package_name: Package name to exclude from results.
        :return: List of tuples (component, bounds).
        """
        excluded_bounds = []
        self._collect_bounds_excluding_package(self.root_component, package_name, excluded_bounds)
        return excluded_bounds

    def _collect_bounds_excluding_package(self, component, package_name, excluded_bounds):
        """
        Recursively collects bounds of components that do not belong to the target package.

        :param component: Current component being evaluated.
        :param package_name: Package name to exclude.
        :param excluded_bounds: List to accumulate excluded bounds.
        """
        if component:
            component_package = component.properties.get("package")
            if component_package != package_name:
                bounds = component.properties.get("bounds")
                if bounds:
                    excluded_bounds.append((component, utils.parse_bounds_str(bounds)))

            for child in component.children:
                self._collect_bounds_excluding_package(child, package_name, excluded_bounds)

    def find_components_containing_bounds(self, boundbox):
        """
        Finds the smallest components whose bounds contain the given bounding box.

        :param boundbox: Tuple (x, y, width, height) representing a visual change region.
        :return: List of UIComponents that contain the region.
        """
        return self._search_containing_components(self.root_component, boundbox[0], boundbox[1], boundbox[2], boundbox[3])

    def _search_containing_components(self, component, x, y, w, h):
        """
        Recursively checks whether the given bounding box is contained in a component,
        and collects the smallest matching components.

        :param component: UIComponent to check containment.
        :param x: Top-left x of bounding box.
        :param y: Top-left y of bounding box.
        :param w: Width of bounding box.
        :param h: Height of bounding box.
        :return: List of components that contain the box.
        """
        if not component:
            return []

        matching_components = []

        if component.bounds and utils.is_contained((x, y, x+w, y+h), component.bounds):
            children_matches = []
            for child in component.children:
                child_results = self._search_containing_components(child, x, y, w, h)
                children_matches.extend(child_results)

            if children_matches:
                return children_matches + matching_components
            matching_components.append(component)

        for child in component.children:
            matching_components.extend(self._search_containing_components(child, x, y, w, h))

        return matching_components
