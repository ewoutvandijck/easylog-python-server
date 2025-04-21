import base64
import io

from PIL import Image, ImageOps


def image_to_base64(image: Image.Image) -> str:
    ImageOps.exif_transpose(image, in_place=True)

    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")

    # Convert the PIL Image to a JPEG format
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    # Encode the image data as base64
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/jpeg;base64,{img_str}"
