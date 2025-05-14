from PIL import Image
import tempfile
from PyShapes import *
import cv2
import numpy as np
import pytesseract

def getTextFromImage(image):
    """
    Extracts textual content from the given image using Tesseract OCR.
    
    :param image: A PIL Image object.
    :return: A string with extracted text, cleaned and line breaks replaced by spaces.
    """
    return pytesseract.image_to_string(image).strip().replace('\n', ' ')

def listTextPixelsFromImage(image):
    """
    Identifies the pixel positions of text in the image. For each recognized word,
    returns a set of pixel coordinates relative to its bounding box.
    
    :param image: A PIL Image object.
    :return: A list of sets, where each set contains (x, y) coordinates of a single word.
    """
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    data = pytesseract.image_to_data(thresh, output_type=pytesseract.Output.DICT)
    relative_text_blocks = []

    for i in range(len(data["text"])):
        word = data["text"][i].strip()
        if word:
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            roi = thresh[y:y+h, x:x+w]

            word_pixels = set()
            for row in range(h):
                for col in range(w):
                    if roi[row, col] == 255:
                        word_pixels.add((col, row))

            if word_pixels:
                relative_text_blocks.append(word_pixels)

    return relative_text_blocks

def getImageContentShape(image):
    """
    Detects the geometric shapes contained within the image using PyShapes.

    :param image: A PIL Image object.
    :return: A list of shape names detected (e.g., 'circle', 'rectangle').
    """
    with tempfile.NamedTemporaryFile(suffix='.png', delete=True) as tmp:
        image.save(tmp.name)
        temp_path = tmp.name

        shapes = PyShape(temp_path)
        shapes_dictionary = shapes.get_all_shapes()
        shapes.close()
        detected_shapes = [key for key, value in shapes_dictionary.items() if value == 1]
        return detected_shapes

def getColorsFromImage(image):
    """
    Extracts the most prominent RGB colors in the image.

    :param image: A PIL Image object.
    :return: A set of RGB tuples representing the dominant colors.
    """
    component = image.convert('RGB')
    min_percentage = 0.5  # Minimum threshold percentage for a color to be included

    all_pixels = component.size[0] * component.size[1]
    colors_hm = {}
    sorted_colors = []

    for rgba_pixel in component.getdata():
        nb = colors_hm.get(rgba_pixel, {'nb': 0})['nb']
        colors_hm[rgba_pixel] = {'nb': nb + 1}

    for color in colors_hm:
        color_percentage = colors_hm[color]['nb'] * 100 / float(all_pixels)
        if color_percentage >= min_percentage:
            sorted_colors.append({'color': color, 'num': color_percentage})

    sorted_colors.sort(key=lambda k: k['num'], reverse=True)

    color_array = []
    for x in sorted_colors:
        color_array.append((x['color'][0], x['color'][1], x['color'][2]))

    return set(color_array)

def is_image_all_black(img):
    """
    Checks whether the given image is entirely black (grayscale value 0 everywhere).

    :param img: A PIL Image object.
    :return: True if all pixels are black, False otherwise.
    """
    grayscale_img = img.convert("L")
    pixels = grayscale_img.getdata()
    return all(pixel == 0 for pixel in pixels)

def addMask(image, rectangles):
    """
    Applies a white mask (rectangle) over the specified areas in the image.

    :param image: A PIL Image object.
    :param rectangles: List of rectangles defined as [(x1, y1, x2, y2), ...].
    :return: A new masked PIL Image.
    """
    from PIL import ImageDraw
    masked_image = Image.new("RGB", image.size)
    masked_image.paste(image, (0, 0))
    draw = ImageDraw.Draw(masked_image)

    for (x1, y1, x2, y2) in rectangles:
        draw.rectangle([x1, y1, x2, y2], outline=None, fill="white")

    return masked_image

def addHighlight(image, rectangles):
    """
    Creates a new image where only the specified rectangles are visible, and all other regions are painted white.

    :param image: A PIL Image object.
    :param rectangles: List of rectangles defined as [(x1, y1, x2, y2), ...].
    :return: A new PIL Image showing only the highlighted regions.
    """
    new_image = Image.new("RGB", image.size, (255, 255, 255))

    for (x1, y1, x2, y2) in rectangles:
        region = image.convert("RGB").crop((x1, y1, x2, y2))
        new_image.paste(region, (x1, y1))

    return new_image

def cropImage(image, rectangle):
    """
    Crops the image to the specified rectangle.

    :param image: A PIL Image object.
    :param rectangle: A tuple (x1, y1, x2, y2) defining the cropping region.
    :return: A cropped PIL Image.
    """
    (x1, y1, x2, y2) = rectangle
    return image.crop((x1, y1, x2, y2))