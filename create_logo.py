from PIL import Image, ImageDraw, ImageFont

# Create a 256x256 transparent image
img = Image.new("RGBA", (256, 256), color=(0, 0, 0, 0))
d = ImageDraw.Draw(img)

# We'll use a default font but scale it up if possible, or just draw rectangles for D and E if we don't have a good font.
# Actually, loading a default TTF might be tricky on minimal environments, let's try default font and resize, or download a font.
# The easiest way is to try to use a standard font path or use default.
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 160)
except IOError:
    font = ImageFont.load_default()

# Draw 'D' in white
d.text((20, 40), "D", font=font, fill=(255, 255, 255, 255))
# Draw 'E' in yellow
d.text((120, 40), "E", font=font, fill=(255, 223, 0, 255))

img.save("frontend/assets/logo.png")
print("Logo created!")
