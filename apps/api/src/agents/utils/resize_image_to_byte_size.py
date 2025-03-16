from io import BytesIO

from PIL import Image

from src.logger import logger


def resize_image_to_byte_size(
    image: Image.Image,
    target_size_bytes: int = 500 * 1024,  # 500KB
    image_format: str = "JPEG",
    quality: int = 85,
    tolerance: float = 0.1,
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
    # Convert RGBA/LA images to RGB with white background
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3] if len(image.split()) > 3 else None)
        image = background

    logger.info(
        f"Starting image resize. Target size: {target_size_bytes} bytes, Format: {image_format}, Quality: {quality}"
    )

    logger.debug(f"Original image dimensions: {image.size}")

    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    def get_size_bytes(max_side: int) -> int:
        # For square images, both dimensions will be max_side
        if aspect_ratio == 1:
            new_width = new_height = max_side
        # For rectangular images, maintain aspect ratio
        elif aspect_ratio > 1:  # width is larger
            new_width = max_side
            new_height = int(max_side / aspect_ratio)
        else:  # height is larger
            new_height = max_side
            new_width = int(max_side * aspect_ratio)

        # Ensure minimum dimensions of 1x1
        new_width = max(1, new_width)
        new_height = max(1, new_height)

        # Create resized image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Get byte size
        buffer = BytesIO()
        resized.save(buffer, format=image_format, quality=quality, optimize=True)
        return buffer.tell()

    # Binary search for the right maximum dimension
    min_side = min(orig_width, orig_height)
    max_side = max(orig_width, orig_height)
    iterations = 0
    min_diff = 1  # minimum difference of 1 pixel
    current_max_side = max_side  # Initialize outside the loop

    while min_side < max_side and (max_side - min_side) > min_diff:
        current_max_side = (min_side + max_side) // 2
        current_size = get_size_bytes(current_max_side)
        iterations += 1

        logger.debug(f"Iteration {iterations}: scale={current_max_side:.3f}, size={current_size} bytes")

        # Check if we're within tolerance
        if abs(current_size - target_size_bytes) <= target_size_bytes * tolerance:
            logger.info(f"Found suitable scale factor after {iterations} iterations")
            break

        if current_size > target_size_bytes:
            max_side = current_max_side
        else:
            min_side = current_max_side

    # Final resize with the same square handling
    if aspect_ratio == 1:
        final_width = final_height = current_max_side
    elif aspect_ratio > 1:
        final_width = current_max_side
        final_height = int(current_max_side / aspect_ratio)
    else:
        final_height = current_max_side
        final_width = int(current_max_side * aspect_ratio)

    # Return the final resized image
    final_image = image.resize((final_width, final_height), Image.Resampling.LANCZOS)
    logger.info(f"Final image dimensions: {final_image.size}")
    return final_image
