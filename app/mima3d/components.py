def text_to_image(text):
    image = text + "image"
    return image

def image_to_text(image):
    text = image + "text"
    return text

modules = {
    "TtI": ("/tti", "Converts text to image", "str", "img", text_to_image),
    "ItT": ("/itt", "Converts image to text", "img", "str", image_to_text)
}
