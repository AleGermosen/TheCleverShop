from PIL import Image, ImageDraw, ImageOps
import os

# Ensure the directory exists
os.makedirs('static/img', exist_ok=True)

# Open the original image
input_path = 'static/img/clevercupid.png'
output_path = 'static/img/clevercupid_round.png'

# Open the image
img = Image.open(input_path)

# Resize to common favicon size (maintaining aspect ratio)
img = img.resize((192, 192), Image.LANCZOS)

# Create a circular mask
mask = Image.new('L', img.size, 0)
draw = ImageDraw.Draw(mask)
draw.ellipse((0, 0, img.size[0], img.size[1]), fill=255)

# Make sure we're working with RGB mode before inverting
if img.mode != 'RGB':
    img = img.convert('RGB')

# Apply color inversion
# img = ImageOps.invert(img)

# Apply the circular mask to the inverted image
result = Image.new('RGBA', img.size, (0, 0, 0, 0))
result.paste(img, (0, 0), mask)

# Save the result
result.save(output_path)
print(f"Round inverted icon created at {output_path}") 