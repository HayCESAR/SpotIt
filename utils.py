def parse_bounds_str(bounds):
    """Parses a bounds string in the format '[x1,y1][x2,y2]' and returns (x1, y1, x2, y2)."""
    import re

    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    if match:
        return tuple(map(int, match.groups()))
    raise ValueError("Invalid bounds format")

def convert_bounds_wh(bounds):
  """Converts the bounds from (x1, y1, x2, y2) to (x, y, w, h)."""
  return (bounds[0], bounds[1], bounds[2]-bounds[0], bounds[3]-bounds[1])

def convert_bounds_xy(bounds):
  """Converts the bounds from (x, y, w, h) to (x1, y1, x2, y2)."""
  return (bounds[0], bounds[1], bounds[0]+bounds[2], bounds[1]+bounds[3])

def is_contained(box1, box2):
  """
  Checks if box1 is fully contained within box2.
  :param box1: Tuple (x1, y1, x2, y2) representing the first bounding box.
  :param box2: Tuple (x1, y1, x2, y2) representing the second bounding box.
  :return: True if box1 is inside box2, False otherwise.
  """
  x1_1, y1_1, x2_1, y2_1 = box1
  x1_2, y1_2, x2_2, y2_2 = box2

  return x1_2 <= x1_1 and y1_2 <= y1_1 and x2_2 >= x2_1 and y2_2 >= y2_1

# def add_missing_elements(list1, list2):
#     """
#     Adds missing elements from list1 to list2 if they are not already present.
#     :param list1: List of objects to check.
#     :param list2: List of objects to update.
#     :return: Updated list2 with missing elements added.
#     """
#     for item in list1:
#         if item not in list2:
#             list2.append(item)
#     return list2