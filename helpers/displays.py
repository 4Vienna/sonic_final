import os
import pygame

# Force the SDL window to open at the top of the screen (x=0, y=0).
# This must be set before creating the display surface.
os.environ.setdefault('SDL_VIDEO_WINDOW_POS', '0,0')

# Get the native screen height from the display
display_info = pygame.display.get_surface() or pygame.display.set_mode((1, 1))
native_height = pygame.display.get_desktop_sizes()[0][1] if pygame.display.get_desktop_sizes() else 448
# Calculate width for 4:3 aspect ratio: width = height * 4 / 3
screen_width = int(native_height * 4 / 3)
screen_height = native_height

screen = pygame.display.set_mode((screen_width, screen_height))

SCREEN_WIDTH, SCREEN_HEIGHT = screen_width, screen_height

pygame.display.set_caption("Sonic 1")