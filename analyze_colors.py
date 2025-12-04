from PIL import Image
import numpy as np

img = Image.open('resources\\zones\\green_hill_1.png')
print(f"Image size: {img.size}")
print(f"Image mode: {img.mode}")

# Convert to RGB
rgb_img = img.convert('RGB')

# Get unique colors
arr = np.array(rgb_img)
pixels = arr.reshape(-1, 3)
unique_colors = np.unique(pixels, axis=0)
print(f"\nTotal unique colors: {len(unique_colors)}")
print(f"\nFirst 15 colors (RGB):")
for color in unique_colors[:15]:
    print(f"  {tuple(color)}")
