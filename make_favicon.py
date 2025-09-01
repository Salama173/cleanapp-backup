from PIL import Image
import os

os.makedirs("static", exist_ok=True)

img = Image.open("logo.png")
img = img.resize((32, 32), Image.LANCZOS)
img.save("static/favicon.ico", format="ICO")
img.save("static/favicon.png", format="PNG")

print("favicon.ico and favicon.png saved in static/ successfully")
