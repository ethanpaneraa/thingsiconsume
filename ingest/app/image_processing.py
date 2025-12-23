from PIL import Image
import io
from typing import Tuple


def convert_to_webp(image_bytes: bytes, quality: int = 90) -> Tuple[bytes, int, int]:
    """
    Convert image bytes to WebP format.

    Args:
        image_bytes: Original image bytes (any format)
        quality: WebP quality (0-100), default 90

    Returns:
        Tuple of (webp_bytes, width, height)
    """
    # Open image from bytes
    image = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if necessary (WebP doesn't support RGBA directly, but PIL handles it)
    if image.mode in ("RGBA", "LA", "P"):
        # Create white background for transparency
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        rgb_image.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
        image = rgb_image
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Get dimensions
    width, height = image.size

    # Convert to WebP
    webp_buffer = io.BytesIO()
    image.save(webp_buffer, format="WEBP", quality=quality, method=6)
    webp_bytes = webp_buffer.getvalue()

    return webp_bytes, width, height

