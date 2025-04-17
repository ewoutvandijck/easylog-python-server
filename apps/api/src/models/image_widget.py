import base64
import io

from PIL import Image, ImageOps
from pydantic import BaseModel


class ImageWidget(BaseModel):
    image: Image.Image

    def to_base64(self) -> str:
        image = ImageOps.exif_transpose(self.image, in_place=False)

        if not image:
            raise ValueError("Image is not valid")

        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGB")

        # Convert the PIL Image to a JPEG format
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)

        # Encode the image data as base64
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return f"data:image/jpeg;base64,{img_str}"
