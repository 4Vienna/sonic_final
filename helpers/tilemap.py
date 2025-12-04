"""
Tile collision system for Sonic game.
Detects tiles by color and determines which are solid.
"""

import pygame
from PIL import Image
import numpy as np

# Tile size (in pixels)
TILE_SIZE = 16

# Color detection system
# Define which RGB colors should be considered solid (collide-able)
# Format: (R, G, B) -> True for solid, False for passable
SOLID_COLORS = {
    # Green grass colors - these are solid
    (34, 136, 68): True,    # Dark green
    (68, 170, 102): True,   # Medium green
    (102, 187, 136): True,  # Light green
    (136, 204, 170): True,  # Very light green
    
    # Brown/dirt colors - solid
    (136, 102, 68): True,   # Brown dirt
    (170, 136, 102): True,  # Light brown
    
    # Sky colors - passable
    (102, 170, 238): False, # Sky blue
    (136, 187, 255): False, # Light sky
    
    # Background/empty - passable
    (0, 0, 0): False,       # Black (empty)
    (255, 0, 255): False,   # Magenta (transparent)
}

# Cache for color detection
_background_image = None
_collision_cache = {}

def load_background_collision_data(image_path):
    """Load and analyze the background image for collision tiles."""
    global _background_image, _collision_cache
    
    img = Image.open(image_path)
    # Convert to RGB
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    _background_image = np.array(img)
    _collision_cache = {}
    print(f"Loaded background collision data: {img.size}")

def get_tile_collision_from_image(pixel_x, pixel_y):
    """
    Check if a pixel position in the background image should be solid.
    Returns True if solid, False if passable.
    """
    if _background_image is None:
        return False
    
    # Clamp to image bounds
    x = max(0, min(pixel_x, _background_image.shape[1] - 1))
    y = max(0, min(pixel_y, _background_image.shape[0] - 1))
    
    # Get the color at this pixel
    color = tuple(_background_image[int(y), int(x)])
    
    # Check cache first
    if color in _collision_cache:
        return _collision_cache[color]
    
    # Determine if this color is solid
    if color in SOLID_COLORS:
        is_solid = SOLID_COLORS[color]
    else:
        # For unknown colors, try to find the closest match
        is_solid = _color_is_solid_fuzzy(color)
    
    _collision_cache[color] = is_solid
    return is_solid

def _color_is_solid_fuzzy(color):
    """
    Use fuzzy matching to determine if a color should be solid.
    This helps handle slight color variations in the tileset.
    """
    r, g, b = color
    
    # Green tones (grass) are typically solid
    if g > r and g > b:
        # Green is dominant
        if g > 100:  # Not too dark
            return True
    
    # Brown tones (dirt) are typically solid
    if r > 100 and b < r and b < g:
        return True
    
    # Blue tones (sky) are passable
    if b > r and b > g:
        return False
    
    # Default to passable for unknown colors
    return False

def check_ground_collision(x, y, width, height):
    """
    Check if sprite at (x, y) with given dimensions collides with solid tiles.
    Returns the Y position where the sprite should be placed (on top of ground).
    """
    if _background_image is None:
        return None
    
    # Check the bottom of the sprite
    bottom_y = y + height
    
    # Check multiple points across sprite width for more accurate collision
    check_points = [
        int(x + width * 0.25),
        int(x + width * 0.5),
        int(x + width * 0.75),
    ]
    
    for check_x in check_points:
        # Check from bottom upward to find the first solid tile
        for check_y in range(int(bottom_y), int(bottom_y) - 50, -1):
            if get_tile_collision_from_image(check_x, check_y):
                # Found solid ground - return position just above it
                collision_y = check_y - height
                return collision_y
    
    return None  # No collision
