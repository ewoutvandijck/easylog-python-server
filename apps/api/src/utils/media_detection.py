from typing import Literal, cast

MediaTypes = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


def guess_media_type(content: str, hint: MediaTypes | None = None) -> MediaTypes:
    if content.startswith("data:image/"):
        try:
            return cast(MediaTypes, content.split(";")[0].split(":")[1])
        except Exception:
            pass

    # Always default to JPEG for Anthropic compatibility
    return hint or "image/jpeg"


def extract_base64_content(content: str) -> str:
    """Extract the base64 content from a data URL string."""
    try:
        # If it's a data URL, extract just the base64 part
        if content.startswith("data:"):
            return content.split(";")[1].split(",")[1]
        # Otherwise return as is (it's assumed to already be base64)
        return content
    except Exception:
        return content
