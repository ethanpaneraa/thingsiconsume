from PIL import Image
import io
from typing import Tuple


def convert_to_webp(image_bytes: bytes, quality: int = 90) -> Tuple[bytes, int, int]:
    image = Image.open(io.BytesIO(image_bytes))

    if image.mode in ("RGBA", "LA", "P"):
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        rgb_image.paste(image, mask=image.split()[-1] if image.mode in ("RGBA", "LA") else None)
        image = rgb_image
    elif image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size

    webp_buffer = io.BytesIO()
    image.save(webp_buffer, format="WEBP", quality=quality, method=6)
    webp_bytes = webp_buffer.getvalue()

    return webp_bytes, width, height

