from io import BytesIO

from PIL import Image

from src.logger import logger


def resize_image_to_byte_size(
    image: Image.Image,
    target_size_bytes: int = 500 * 1024,  # 500KB
    image_format: str = "JPEG",
    quality: int = 85,
    tolerance: float = 0.1,
    min_side: int = 500,  # Minimum dimension of 500 pixels
    max_side: int = 1500,  # Maximum dimension of 1500 pixels
) -> Image.Image:
    """
    Resize an image to approximately match a target file size in bytes.
    Only applies transformations if the original image doesn't meet the target size.

    Args:
        image: PIL Image object
        target_size_bytes: Desired file size in bytes
        image_format: Output format (JPEG, PNG, etc.)
        quality: Initial JPEG quality (if applicable)
        tolerance: Acceptable deviation from target size (0.1 = 10%)
        min_side: Minimum dimension for any side of the image (default: 500px)
        max_side: Maximum dimension for any side of the image (default: 1500px)

    Returns:
        Resized PIL Image object or original if already within target size
    """
    logger.info(
        f"Starting image resize. Target size: {target_size_bytes} bytes, Format: {image_format}, Quality: {quality}"
    )

    # Check if the original image is already within the target size range
    buffer = BytesIO()
    image.save(buffer, format=image_format, quality=quality, optimize=True)
    original_size = buffer.tell()
    logger.info(f"Original image size: {original_size} bytes, dimensions: {image.size}")

    # If image is already within tolerance of target size, return it unchanged
    if abs(original_size - target_size_bytes) <= target_size_bytes * tolerance:
        logger.info(f"Original image already within target size range ({original_size} bytes). No resize needed.")
        return image

    # If image is smaller than target and enlarging is not desired, return it as is
    if original_size < target_size_bytes:
        logger.info(f"Original image ({original_size} bytes) is smaller than target size. No resize needed.")
        return image

    # Convert RGBA/LA images to RGB with white background only if needed
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3] if len(image.split()) > 3 else None)
        image = background

    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # Cache for already computed sizes to avoid redundant operations
    size_cache = {}

    def get_size_bytes(max_side: int) -> int:
        # Check cache first
        if max_side in size_cache:
            return size_cache[max_side]

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
        size = buffer.tell()

        # Cache the result
        size_cache[max_side] = size
        return size

    # Binary search for the right maximum dimension
    binary_search_min = min_side  # Use the provided min_side parameter
    binary_search_max = min(max_side, max(orig_width, orig_height))  # Respect the max_side parameter

    # For faster convergence, check endpoints first
    min_size = get_size_bytes(binary_search_min)
    max_size = get_size_bytes(binary_search_max)

    # If target is outside our range, return closest endpoint
    if target_size_bytes <= min_size:
        logger.info(f"Using minimum size ({binary_search_min}px) which produces {min_size} bytes")
        current_max_side = binary_search_min
    elif target_size_bytes >= max_size:
        logger.info(f"Using maximum size ({binary_search_max}px) which produces {max_size} bytes")
        current_max_side = binary_search_max
    else:
        # Standard binary search with early termination
        iterations = 0
        min_diff = 1  # minimum difference of 1 pixel
        current_max_side = binary_search_max  # Initialize outside the loop
        max_iterations = 10  # Limit iterations to prevent excessive processing

        while binary_search_min < binary_search_max and (binary_search_max - binary_search_min) > min_diff:
            if iterations >= max_iterations:
                logger.info(f"Reached maximum iterations ({max_iterations}). Using current best value.")
                break

            current_max_side = (binary_search_min + binary_search_max) // 2
            current_size = get_size_bytes(current_max_side)
            iterations += 1

            logger.info(f"Iteration {iterations}: scale={current_max_side}, size={current_size} bytes")

            # Check if we're within tolerance
            if abs(current_size - target_size_bytes) <= target_size_bytes * tolerance:
                logger.info(f"Found suitable scale factor after {iterations} iterations")
                break

            if current_size > target_size_bytes:
                binary_search_max = current_max_side
            else:
                binary_search_min = current_max_side

    # Final resize with the same square handling
    if aspect_ratio == 1:
        final_width = final_height = current_max_side
    elif aspect_ratio > 1:
        final_width = current_max_side
        final_height = int(current_max_side / aspect_ratio)
    else:
        final_height = current_max_side
        final_width = int(current_max_side * aspect_ratio)

    # Return the final resized image - check if we already have it in cache
    if current_max_side in size_cache:
        logger.info(f"Using cached resized image with dimensions: ({final_width}, {final_height})")
        final_image = image.resize((final_width, final_height), Image.Resampling.LANCZOS)
    else:
        final_image = image.resize((final_width, final_height), Image.Resampling.LANCZOS)

    logger.info(f"Final image dimensions: {final_image.size}")
    return final_image
