# Extension Icons

This folder should contain the extension icons in the following sizes:

- `icon16.png` - 16x16 pixels
- `icon48.png` - 48x48 pixels
- `icon128.png` - 128x128 pixels

You can create these icons using any image editor. For a quick start, you can:

1. Use an online icon generator
2. Create simple colored squares with text
3. Use a tool like GIMP, Photoshop, or Figma

For now, you can use placeholder icons or create simple ones with your brand colors.

## Quick Icon Creation

You can use this Python script to generate simple placeholder icons:

```python
from PIL import Image, ImageDraw, ImageFont

def create_icon(size, filename):
    img = Image.new('RGB', (size, size), color='#4CAF50')
    draw = ImageDraw.Draw(img)

    # Add text
    text = "WIC"
    try:
        font = ImageFont.truetype("Arial", size // 3)
    except:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, text, fill='white', font=font)

    img.save(filename)

create_icon(16, 'icon16.png')
create_icon(48, 'icon48.png')
create_icon(128, 'icon128.png')
```

Or use an online service like:

- https://www.favicon-generator.org/
- https://realfavicongenerator.net/
