from PIL import Image

def addMask(image, rectangles):
    """
    Masks an image by drawing black rectangles over specified regions.

    :param image: PIL Image object.
    :param rectangles: List of rectangles, each defined as [(x1, y1, x2, y2)].
    :return: Masked PIL Image.
    """
    from PIL import ImageDraw
    # Convert image to editable mode
    masked_image = Image.new("RGB", image.size)
    masked_image.paste(image, (0, 0))
    draw = ImageDraw.Draw(masked_image)

    # Apply mask (black rectangles)
    for (x1, y1, x2, y2) in rectangles:
        draw.rectangle([x1, y1, x2, y2], outline=None, fill="red")

    return masked_image

def addHighlight(image, rectangles):
    """
    Paints the entire image black except for the given list of rectangles.

    :param image: PIL Image object.
    :param rectangles: List of rectangles, each defined as [(x1, y1), (x2, y2)].
    :return: Processed PIL Image.
    """
    # Create a black image of the same size
    new_image = Image.new("RGB", image.size, (0, 0, 0))

    # Paste only the given rectangles from the original image
    for (x1, y1, x2, y2) in rectangles:
        region = image.convert("RGB").crop((x1, y1, x2, y2))  # Crop the region from original image
        new_image.paste(region, (x1, y1))  # Paste it onto the black image

    return new_image

def removeBackground(image):
    """
    Removes the background from an image using OpenCV.

    :param image: PIL Image object.
    :return: PIL Image with the background removed (transparent PNG).
    """
    import numpy as np
    import cv2

    # Convert PIL Image to OpenCV format
    open_cv_image = np.array(image.convert("RGB"))
    open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    # Apply Otsu's thresholding
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours and create mask
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(thresh)

    # Draw filled contours to create a mask of the object
    cv2.drawContours(mask, contours, -1, (255), thickness=cv2.FILLED)

    # Convert mask to 3 channels
    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    # Remove background using the mask
    result = cv2.bitwise_and(open_cv_image, mask)

    # Convert black background to transparent
    b, g, r = cv2.split(result)
    alpha = mask[:, :, 0]  # Use mask as alpha channel
    rgba = cv2.merge((b, g, r, alpha))

    # Convert back to PIL format
    transparent_image = Image.fromarray(cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA))

    return transparent_image

def removeText(image):
    import pytesseract
    import numpy as np
    import cv2
    import math

    def midpoint(x1, y1, x2, y2):
        x_mid = int((x1 + x2)/2)
        y_mid = int((y1 + y2)/2)
        return (x_mid, y_mid)

    image_np = np.array(image)
    image_cv2 = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    h = image_cv2.shape[0]
    boxes = pytesseract.image_to_boxes(image)

    mask = np.zeros(image_cv2.shape[:2], dtype="uint8")
    for b in boxes.splitlines():
        b = b.split(' ')
        left=int(b[1])
        bottom=h-int(b[4])
        right=int(b[3])
        top=h-int(b[2])

        x_mid0, y_mid0 = midpoint(left, top, left, bottom)
        x_mid1, y_mi1 = midpoint(right, top, right, bottom)

        thickness = int(math.sqrt( (right - left)**2 + (top - bottom)**2 ))

        #Define the line and inpaint
        cv2.line(mask, (x_mid0, y_mid0), (x_mid1, y_mi1), 255, thickness)
        inpainted_img = cv2.inpaint(image_cv2, mask, 7, cv2.INPAINT_NS)

        image_rgb = cv2.cvtColor(inpainted_img, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        pil_image = Image.fromarray(image_rgb)

    return(pil_image)