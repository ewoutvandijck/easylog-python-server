import base64
import io

from PIL import Image

from src.logger import logger


def decode_data_url_to_image(data_url: str) -> Image.Image:
    """
    Convert a data URL to a PIL Image object.

    Args:
        data_url (str): The data URL string containing the image data
            (e.g., "data:image/jpeg;base64,/9j/4AAQSkZJRg...")

    Returns:
        Optional[Image.Image]: PIL Image object if successful, None if conversion fails
    """
    try:
        # Extract the base64 encoded data from the URL
        _, encoded = data_url.split(",", 1)

        # Decode the base64 data
        binary_data = base64.b64decode(encoded)

        # Create a bytes buffer from the decoded data
        buffer = io.BytesIO(binary_data)

        # Open the image using PIL
        image = Image.open(buffer)

        return image
    except Exception as e:
        logger.error(f"Error converting data URL {data_url} to image: {str(e)}", exc_info=True)
        raise e


def encode_image_to_data_url(image: Image.Image) -> str:
    """
    Convert a PIL Image object to a data URL string.

    Args:
        image (Image.Image): The PIL Image object to convert
        format (str): The image format to use for encoding (default: "JPEG")

    Returns:
        str: Data URL string containing the encoded image
            (e.g., "data:image/jpeg;base64,/9j/4AAQSkZJRg...")
    """
    try:
        # Create a bytes buffer to store the image data
        buffer = io.BytesIO()

        # Save the image to the buffer
        image.save(buffer)

        # Get the binary data from the buffer
        binary_data = buffer.getvalue()

        # Encode the binary data as base64
        encoded_data = base64.b64encode(binary_data).decode("utf-8")

        # Create the data URL string
        mime_type = f"image/{image.format or 'jpeg'}".lower()
        data_url = f"data:{mime_type};base64,{encoded_data}"

        return data_url
    except Exception as e:
        logger.error(f"Error converting image to data URL: {str(e)}", exc_info=True)
        raise e
