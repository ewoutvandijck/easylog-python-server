from io import BytesIO

from PIL import Image

from src.logger import logger


def resize_image_to_byte_size(
    image: Image.Image, target_size_bytes: int, image_format: str = "JPEG", quality: int = 85, tolerance: float = 0.1
) -> Image.Image:
    """
    Resize an image to approximately match a target file size in bytes.

    Args:
        image: PIL Image object
        target_size_bytes: Desired file size in bytes
        image_format: Output format (JPEG, PNG, etc.)
        quality: Initial JPEG quality (if applicable)
        tolerance: Acceptable deviation from target size (0.1 = 10%)

    Returns:
        Resized PIL Image object
    """
    logger.info(
        f"Starting image resize. Target size: {target_size_bytes} bytes, Format: {image_format}, Quality: {quality}"
    )

    logger.debug(f"Original image dimensions: {image.size}")

    min_scale = 0.01  # Minimum scale factor
    max_scale = 1.0  # Maximum scale factor

    orig_width, orig_height = image.size

    def get_size_bytes(scale: float) -> int:
        # Calculate new dimensions
        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        # Ensure minimum dimensions of 1x1
        new_width = max(1, new_width)
        new_height = max(1, new_height)

        # Create resized image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Get byte size
        buffer = BytesIO()
        resized.save(buffer, format=image_format, quality=quality)
        return buffer.tell()

    # Binary search for the right scale factor
    scale = 1.0
    iterations = 0
    while min_scale < max_scale:
        scale = (min_scale + max_scale) / 2
        current_size = get_size_bytes(scale)
        iterations += 1

        logger.debug(f"Iteration {iterations}: scale={scale:.3f}, size={current_size} bytes")

        # Check if we're within tolerance
        if abs(current_size - target_size_bytes) <= target_size_bytes * tolerance:
            logger.info(f"Found suitable scale factor after {iterations} iterations")
            break

        if current_size > target_size_bytes:
            max_scale = scale
        else:
            min_scale = scale

    # Return the final resized image
    new_width = max(1, int(orig_width * scale))
    new_height = max(1, int(orig_height * scale))
    final_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    logger.info(f"Final image dimensions: {final_image.size}")
    return final_image
