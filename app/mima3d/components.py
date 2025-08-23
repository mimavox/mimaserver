def text_to_image(text):
    image = text + "image"
    return image

def image_to_text(image):
    text = image + "text"
    return text

modules = {
    "IN": ("Sensor input", "img", "img", None),
    "OUT": ("Action output", "img", "Action", None),
    "TtI": ("Converts text to image", "str", "img", text_to_image),
    "ItT": ("Converts image to text", "img", "str", image_to_text)
}
