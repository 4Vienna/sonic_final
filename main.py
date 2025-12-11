import pygame
from sprites_code.sprite_classes import *
from helpers.displays import screen, SCREEN_WIDTH, SCREEN_HEIGHT
from sprites_code.build_background import TileMap
from sprites_code.sprite_manager import get_sprite_data

# Load background image
background_img = pygame.image.load('resources/backgrounds/green_hill_zone.png').convert_alpha()
bg_width, bg_height = background_img.get_size()
# Camera offset (world x position of left edge of screen)
camera_x = 0

pygame.init()

#time variables
start_time = pygame.time.get_ticks()
last_update = pygame.time.get_ticks()
clock = pygame.time.Clock()
FPS = 60

# Compute Sonic scale so his on-screen height matches original proportion
# Original: Sonic was 48 px tall on a 480 px screen -> 10% of screen height
target_ratio_of_screen = 48 / 480.0
data = get_sprite_data('sonic_idle')
if data is not None:
    src_height = data[3]
    desired_height_px = SCREEN_HEIGHT * target_ratio_of_screen
    scale_ratio = desired_height_px / float(src_height)
else:
    # fallback to existing default if CSV missing
    scale_ratio = 2

sonic = Sonic(scale_ratio)
# Player state: lives and simple invulnerability timer after being hit
sonic.invulnerable_until = 0

enemies = [MotoBug(scale_ratio, 300)]
bullets = []
player_move = False

# Load tilemap for zone; render at source tile size then scale by `scale_ratio`
map_csv = 'resources/zones/green_hill_1/green_hill_1_map.csv'
tileset_path = 'resources/zones/green_hill_1/green_hill_1_tiles.png'
tilemap = TileMap(map_csv,
                  tileset_path,
                  tile_size=16,
                  scale=scale_ratio)

# Set level/world width now that tilemap is loaded so sprites use correct bounds
level_width = max(bg_width, getattr(tilemap, 'map_width', bg_width))
set_level_width(level_width)

# Also determine level height (for vertical camera clamping)
level_height = max(bg_height, getattr(tilemap, 'map_height', bg_height))

# Set a fixed ground level and remove ground tiles visually from the tilemap
# User requested a fixed ground y position of 400 pixels
ground_level = 400

# compute Sonic display height so we can compute the tile y that corresponds
try:
    src_data = get_sprite_data('sonic_idle')
    src_h = src_data[3] if src_data is not None else 48
    sonic_display_h = int(src_h * scale_ratio)
except Exception:
    sonic_display_h = int(48 * scale_ratio)

# Compute the pixel y of the top of the tile layer that would sit under Sonic
ground_pixel_top = ground_level + sonic_display_h

# Clear tilemap pixels at and below the computed ground_pixel_top so ground tiles are removed
try:
    if getattr(tilemap, 'map_surface', None) is not None:
        rect_y = max(0, int(ground_pixel_top))
        rect_h = max(0, int(tilemap.map_height - rect_y))
        tilemap.map_surface.fill((0, 0, 0, 0), rect=(0, rect_y, int(tilemap.map_width), rect_h))
except Exception:
    pass

# Clamp ground_level to level bounds and apply to Sonic and existing enemies
ground_level = max(0, min(ground_level, int(level_height - sonic_display_h)))
sonic.GROUND_LEVEL = ground_level
# place Sonic on the ground at start
sonic.y = ground_level
for e in enemies:
    try:
        e.GROUND_LEVEL = ground_level
        # position enemies on the ground as well
        e.y = ground_level
    except Exception:
        pass




def display_text(text, font_size, position, color=(255, 255, 255)):
    font = pygame.font.SysFont(None, font_size)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, position)


running = True
while running:
    # store previous vertical position for collision detection (stomp)
    sonic.prev_y = sonic.y

    #Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        keys = pygame.key.get_pressed()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if keys[pygame.K_RIGHT]:
                player_move = True
                sonic.x_change = 12
                if sonic.speed <= 0 and sonic.direction == "left":
                    sonic.move_type = "skid"
                    sonic.x_change = 128
                else:
                    sonic.move_type = "walk"
                # leaving idle; reset idle timer
                sonic.idle_start_time = None
            if keys[pygame.K_LEFT]:
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
            if keys[pygame.K_DOWN]:
                if sonic.move_type != "crouch" and sonic.x_change == 0 and sonic.speed == 0:
                    sonic.move_type = "crouch"
                    sonic.x_change = 0
                    # leaving idle; reset idle timer
                    sonic.idle_start_time = None
                            
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
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
            
    # Update clock time in seconds and minutes
    current_time = pygame.time.get_ticks()
    elapsed_time = (current_time - start_time) // 1000   

    minutes = elapsed_time // 60
    seconds = elapsed_time % 60     

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
        

    sonic.animation()
    screen.fill((0, 146, 255))
    # Camera behavior:
    # Horizontal: center Sonic once he passes half the screen, clamp to level bounds
    max_camera_x = max(0, level_width - SCREEN_WIDTH)
    half_screen = SCREEN_WIDTH // 2
    if sonic.x <= half_screen:
        camera_x = 0
    else:
        camera_x = sonic.x - half_screen
        if camera_x > max_camera_x:
            camera_x = max_camera_x

    # Vertical: follow Sonic's vertical position (center on his midpoint), clamp to level bounds
    max_camera_y = max(0, level_height - SCREEN_HEIGHT)
    half_screen_y = SCREEN_HEIGHT // 2
    try:
        sonic_mid = int(sonic.y + (getattr(sonic, 'height', 0) * sonic.ratio) / 2)
    except Exception:
        sonic_mid = int(sonic.y)
    if sonic_mid <= half_screen_y:
        camera_y = 0
    else:
        camera_y = sonic_mid - half_screen_y
        if camera_y > max_camera_y:
            camera_y = max_camera_y

    # Draw background offset by camera (x,y)
    screen.blit(background_img, (-int(camera_x), -int(camera_y)))
    # Draw tilemap (pre-rendered) with same camera offset so tiles scroll
    if 'tilemap' in globals() and getattr(tilemap, 'map_surface', None) is not None:
        screen.blit(tilemap.map_surface, (-int(camera_x), -int(camera_y)))
    
    # Convert world coordinates to screen coordinates using camera_x and camera_y
    sonic_screen_x = int(sonic.x - camera_x)
    sonic_screen_y = int(sonic.y - camera_y)
    sonic.draw(screen, (sonic_screen_x, sonic_screen_y))
    for enemy in enemies:
        enemy_screen_x = int(enemy.x - camera_x)
        enemy_screen_y = int(enemy.y - camera_y)
        bullet = enemy.move(sonic)
        if bullet is not None:
            bullets.append(bullet)
        if bullets:
            # iterate over a copy so we can remove bullets safely while iterating
            for bullet in bullets[:]:
                bullet_screen_x = int(bullet.x - camera_x)
                bullet.move(sonic)
                bullet_screen_y = int(bullet.y - camera_y)
                bullet.draw(screen, (bullet_screen_x, bullet_screen_y))

                # Build rects for a reliable collision test (world coords)
                try:
                    sonic_rect = pygame.Rect(sonic_screen_x, int(sonic_screen_y), int(sonic.width * sonic.ratio), int(sonic.height * sonic.ratio))
                    bullet_rect = pygame.Rect(bullet_screen_x, int(bullet_screen_y), int(bullet.width * bullet.ratio), int(bullet.height * bullet.ratio))
                except Exception:
                    sonic_rect = None
                    bullet_rect = None

                # If rects collide, treat as a hit and remove the bullet
                if sonic_rect is not None and bullet_rect is not None and sonic_rect.colliderect(bullet_rect):
                    # Let existing collision handler process damage/knockback
                    sonic.enemy_collision(bullet, sonic_screen_x, sonic_screen_y, bullet_screen_x, bullet_screen_y)
                    print("Sonic hit by bullet!")
                    try:
                        bullets.remove(bullet)
                    except ValueError:
                        pass
                    continue

                # Remove bullets that left level horizontally or have hit the ground
                if bullet.x < 0 or bullet.x > bg_width or getattr(bullet, 'y', 0) >= ground_level:
                    try:
                        bullets.remove(bullet)
                    except ValueError:
                        pass
               

        hit = sonic.enemy_collision(enemy, sonic_screen_x, sonic_screen_y, enemy_screen_x, enemy_screen_y)
        if hit is not None:
            # Handle enemy defeat logic here
            enemies.remove(hit)
            print(f"Enemies left: {enemies}")
            print(f"Defeated {hit.name}!")
        enemy.draw(screen, (enemy_screen_x, enemy_screen_y))

    # Display score, time, rings
    info = [f"SCORE {sonic.score}", f"TIME {minutes:02d}:{seconds:02d}", f"RINGS {sonic.rings}"]
    for i, text in enumerate(info):
        display_text(text, 30, (0, 5 + (i*30)))

    pygame.display.flip()
    clock.tick(FPS)