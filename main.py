import pygame
from sprites_code.sprite_classes import *
from helpers.displays import screen, SCREEN_WIDTH, SCREEN_HEIGHT
from sprites_code.build_background import TileMap

# Load background image
background_img = pygame.image.load('resources/backgrounds/green_hill_zone.png').convert_alpha()
bg_width, bg_height = background_img.get_size()
# Camera offset (world x position of left edge of screen)
camera_x = 0

pygame.init()



sonic = Sonic(2)
moto = MotoBug(2, 400)
bomb = bomber(800, 300, 2)
player_move = False

# Load tilemap for zone
tilemap = TileMap('resources/zones/green_hill_1/green_hill_1_map.csv',
                  'resources/zones/green_hill_1/green_hill_1_tiles.png',
                  tile_size=16)


last_update = pygame.time.get_ticks()


text_set = pygame.font.SysFont(None, 30)

clock = pygame.time.Clock()
FPS = 60
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        keys = pygame.key.get_pressed()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if keys[pygame.K_d]:
                player_move = True
                sonic.x_change = 12
                if sonic.speed <= 0 and sonic.direction == "left":
                    sonic.move_type = "skid"
                    sonic.x_change = 128
                else:
                    sonic.move_type = "walk"
                # leaving idle; reset idle timer
                sonic.idle_start_time = None
            if keys[pygame.K_a]:
                player_move = True
                sonic.x_change = -12
                if sonic.speed >= 0 and sonic.direction == "right":
                    sonic.move_type = "skid"
                    sonic.x_change = -128
                else:
                    sonic.move_type = "walk"
                # leaving idle; reset idle timer
                sonic.idle_start_time = None
            if event.key == pygame.K_SPACE:
                sonic.jump()
                # leaving idle; reset idle timer
                sonic.idle_start_time = None
            if keys[pygame.K_s]:
                if sonic.move_type != "crouch" and sonic.x_change == 0 and sonic.speed == 0:
                    sonic.move_type = "crouch"
                    sonic.x_change = 0
                    # leaving idle; reset idle timer
                    sonic.idle_start_time = None
                    
                    
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d or event.key == pygame.K_a:
                player_move = False
                if "push" in sonic.state:
                    sonic.speed = 0 
                    sonic.x_change = 0
                elif sonic.speed > 0:
                    sonic.x_change = -12
                elif sonic.speed < 0:
                    sonic.x_change = 12
                else:
                    sonic.x_change = 0
            if event.key == pygame.K_s:
                if sonic.move_type == "crouch":
                    sonic.move_type = None
                    sonic.x_change = 0
            

    # Always update movement while player is actively moving or while
    # Sonic is in the air (jumping) so gravity is applied.
    if player_move or getattr(sonic, 'is_jumping', False): 
        sonic.move()
    else:
        if abs(sonic.speed) != 0:
            if "push" in sonic.state:
                sonic.speed = 0 
                sonic.x_change = 0
            sonic.move()
        elif sonic.move_type == "crouch":
            sonic.set_state("crouch")
            sonic.x_change = 0
        elif abs(sonic.speed) == 0:
            sonic.move_type = None
            sonic.set_state("idle")
            sonic.x_change = 0
            sonic.frame = 0
            # start idle timer now
            sonic.idle_start_time = pygame.time.get_ticks()
        
    moto.move(sonic)

    sonic.animation()
    screen.fill((0, 146, 255))
    # Update camera based on Sonic's speed to create scrolling effect
    # Move camera opposite to Sonic's movement so background scrolls as he runs
    camera_x += sonic.speed
    # Clamp camera within background bounds
    max_camera_x = max(0, bg_width - SCREEN_WIDTH)
    if camera_x < 0:
        camera_x = 0
    elif camera_x > max_camera_x:
        camera_x = max_camera_x

    # Draw background offset by camera
    screen.blit(background_img, (-int(camera_x), 0))
    # Draw tilemap (pre-rendered) with same camera offset so tiles scroll
    if 'tilemap' in globals() and getattr(tilemap, 'map_surface', None) is not None:
        screen.blit(tilemap.map_surface, (-int(camera_x), 0))
    text_surface = text_set.render(f"Sonic position: {sonic.x} direction: {sonic.direction} speed: {sonic.speed} change: {sonic.x_change} state: {sonic.move_type} frame: {sonic.frame}", True, (255,255,255))
    text_rect = text_surface.get_rect(topleft=(0, 0))
    
    sonic.draw(screen, (sonic.x, sonic.y))
    bomb.draw(screen, (bomb.x, bomb.y))
    moto.draw(screen, (moto.x, moto.y))
    screen.blit(text_surface, text_rect)

    pygame.display.flip()
    clock.tick(FPS)