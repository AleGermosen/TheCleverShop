from PIL import Image, ImageDraw, ImageFont
import os

# Create the directory if it doesn't exist
os.makedirs('static/img', exist_ok=True)

# Create a blank image
width, height = 300, 300
img = Image.new('RGB', (width, height), color=(200, 200, 200))

# Draw some text on it
draw = ImageDraw.Draw(img)
text = "Image\nPlaceholder"
text_color = (100, 100, 100)

# Calculate text position (center of image)
textsize = draw.textsize(text) if hasattr(draw, 'textsize') else (100, 50)  # Fallback size
text_x = (width - textsize[0]) // 2
text_y = (height - textsize[1]) // 2

# Draw the text
draw.text((text_x, text_y), text, fill=text_color)

# Save the image
img.save('static/img/placeholder.png')

print("Placeholder image created successfully at static/img/placeholder.png") 