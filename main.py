import pygame
from sprites_code.sprite_classes import *
from helpers.displays import screen, SCREEN_WIDTH, SCREEN_HEIGHT
from sprites_code.build_background import TileMap
from sprites_code.sprite_manager import get_sprite_data
from helpers.instructions import Instructions

# Load background image
background_img = pygame.image.load('resources/backgrounds/green_hill_zone.png').convert_alpha()
bg_width, bg_height = background_img.get_size()
# Camera offset (world x position of left edge of screen)
camera_x = 0
camera_y = 0

pygame.init()

#time variables
start_time = pygame.time.get_ticks()
last_update = pygame.time.get_ticks()
clock = pygame.time.Clock()
FPS = 60

#Set scale ratio based on desired Sonic height on screen
target_ratio_of_screen = 48 / 480.0
data = get_sprite_data('sonic_idle')
if data is not None:
    src_height = data[3]
    desired_height_px = SCREEN_HEIGHT * target_ratio_of_screen
    scale_ratio = desired_height_px / float(src_height)
else:
    # fallback to existing default if CSV missing
    scale_ratio = 2


# Create game objects
sonic = Sonic(scale_ratio)
sonic.set_data()
enemies = [MotoBug(scale_ratio, 500), MotoBug(scale_ratio, 2000), MotoBug(scale_ratio, 3500), MotoBug(scale_ratio, 5000)]
bullets = []
rings = []

for x in range(5):
    ring = Rings(scale_ratio, 400 + x * 150)
    rings.append(ring)

for x in range(5):
    ring = Rings(scale_ratio, 2500 + x * 150)
    rings.append(ring)

for x in range(5):
    ring = Rings(scale_ratio, 4500 + x * 150)
    rings.append(ring)

# Create Words object for score display
word_score = Words(scale_ratio, "score")
word_time = Words(scale_ratio, "time")
word_rings = Words(scale_ratio, "rings")
# Use Words so the correct font/spritesheet is loaded for the lives box
lives_box = Words(scale_ratio, "lives_box")
number_sprites = []
# include 0-9
for num in range(10):
    number_sprites.append(Words(scale_ratio, f"{num}"))
# add colon sprite for time display
number_sprites.append(Words(scale_ratio, ":"))

def build_numbers(number):
    s = str(number)
    sprites = []
    for ch in s:
        if ch in [":", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]:
            try:
                sprites.append(Words(scale_ratio, ch))
            except Exception:
                sprites.append(number_sprites[0])
    return sprites

def show_numbers(word, number):
    numbers_start_x = word.width +15
    number_sprites_list = build_numbers(number)
    # Draw each number next to the previous one using each sprite's displayed width
    cur_x = numbers_start_x
    for num_sprite in number_sprites_list:
        if word.name == "lives_box":
            num_sprite.draw(screen, (word.x + (word.width *.75 ), word.y + (word.height *.5 )))
        else:
            num_sprite.draw(screen, (cur_x, word.y))
        num_sprite.set_dimensions()
        cur_x += num_sprite.x + num_sprite.width 


#Game over text
font = pygame.font.SysFont('Arial', int(48 * scale_ratio))
text_surface = font.render('Game Over', True, (255, 0, 0))
text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
restart_font = pygame.font.SysFont('Arial', int(24 * scale_ratio))
restart_surface = restart_font.render('Press R to Restart or ESC to Quit', True, (255, 255, 255))
restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2) + int(50 * scale_ratio)))
# Player states
sonic.invulnerable_until = 0
player_move = False

# Load tilemap for zone; render at source tile size then scale by `scale_ratio`
# Use testing map and world tileset as requested
map_csv = 'resources/zones/testing.csv'
tileset_path = 'resources/zones/world_tileset.png'
tilemap = TileMap(map_csv,
                  tileset_path,
                  tile_size=16,
                  scale=scale_ratio)

# Place the tilemap so its bottom aligns with the bottom of the play area (screen)
# Compute the map's world origin (top-left) such that bottom-left of the map
# equals bottom-left of the play area.
tilemap.map_origin_x = 0
tilemap.map_origin_y = SCREEN_HEIGHT - getattr(tilemap, 'map_height', bg_height)

# Expose tilemap to the sprite_classes module so its collision code can query tiles
try:
    import sprites_code.sprite_classes as sc
    sc.tilemap = tilemap
except Exception:
    pass

# Set level/world width now that tilemap is loaded so sprites use correct bounds
level_width = max(bg_width, getattr(tilemap, 'map_width', bg_width))
set_level_width(level_width)

# Also determine level height (for vertical camera clamping). Use the map origin
# plus its height so vertical bounds include the placed tilemap.
level_height = max(bg_height, tilemap.map_origin_y + getattr(tilemap, 'map_height', bg_height))

# Compute Sonic display height so we can compute the tile y that corresponds
# Prefer the already-initialized `sonic.height` (set by `sonic.set_data()` above)
try:
    sonic_display_h = int(getattr(sonic, 'height', 48) * scale_ratio)
except Exception:
    sonic_display_h = int(48 * scale_ratio)

# Set ground level based on the tilemap height so Sonic stands on the tiles
# Ground is at the bottom of the placed tilemap; position Sonic so his feet align with that
tilemap_height = getattr(tilemap, 'map_height', level_height)
tilemap_world_y = int(getattr(tilemap, 'map_origin_y', 0))
ground_level = max(0, int(tilemap_world_y + tilemap_height - sonic_display_h))

# Apply ground_level to sprites
def find_platform_y_for_sprite(sprite, world_x=None):
    """Find the top Y (sprite.y) so the sprite stands on the first solid tile under world_x.

    If no solid tile is found we fall back to the `ground_level` computed from the
    bottom of the tilemap.
    """
    # default fallback
    try:
        fallback = int(ground_level)
    except Exception:
        fallback = 0

    # ensure tilemap exists
    if not ('tilemap' in globals() and getattr(tilemap, 'map_surface', None) is not None):
        return fallback

    try:
        tile_h = int(tilemap.tile_size * tilemap.scale)
    except Exception:
        tile_h = tilemap.tile_size

    origin_y = int(getattr(tilemap, 'map_origin_y', 0))

    # Use sprite center X if not provided
    try:
        if world_x is None:
            sprite_w = int(getattr(sprite, 'width', 0) * scale_ratio)
            mid_x = int(getattr(sprite, 'x', 0) + max(1, sprite_w) // 2)
        else:
            mid_x = int(world_x)
    except Exception:
        mid_x = int(getattr(sprite, 'x', 0))

    # Scan rows from top to bottom and place sprite on the first solid tile encountered
    rows = len(getattr(tilemap, 'map_array', []))
    for row in range(rows):
        tile_top = origin_y + row * tile_h
        # sample inside the tile to determine solidity
        sample_y = tile_top + 1
        try:
            if tilemap.is_solid_at(mid_x, sample_y):
                # place sprite so its bottom matches the tile top
                try:
                    sprite_h = int(getattr(sprite, 'height', 0) * scale_ratio)
                except Exception:
                    sprite_h = int(48 * scale_ratio)
                return tile_top - sprite_h
        except Exception:
            continue

    return fallback

# Position Sonic and enemies on the nearest platform under their X coordinates
sonic.GROUND_LEVEL = ground_level
sonic.y = find_platform_y_for_sprite(sonic, world_x=getattr(sonic, 'x', 0))

for e in enemies:
    try:
        # ensure sprite size info is available
        e.set_data()
    except Exception:
        pass
    try:
        e.GROUND_LEVEL = ground_level
        e.y = find_platform_y_for_sprite(e, world_x=getattr(e, 'x', 0))
    except Exception:
        e.y = ground_level




running = True
# Start with instructions shown on launch
show_instructions = True
while running:
    # store previous vertical position for collision detection (stomp)
    sonic.prev_y = sonic.y

    #Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        keys = pygame.key.get_pressed()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and sonic.life <= 0:
                sonic = Sonic(scale_ratio)
                enemies = [MotoBug(scale_ratio, 300)]
                bullets = []
                start_time = pygame.time.get_ticks()
                player_move = False

            if event.key == pygame.K_i:
                # Toggle instructions mode (freeze game and show overlay)
                show_instructions = not show_instructions
            if event.key == pygame.K_ESCAPE:
                running = False
            if keys[pygame.K_RIGHT]:
                player_move = True
                sonic.x_change = 12
                if sonic.speed <= 0 and sonic.direction == "left":
                    sonic.move_type = "skid"
                    sonic.x_change = 128
                elif sonic.state.startswith("roll_"):
                    sonic.move_type = "roll"
                elif sonic.state == "crouch":
                    sonic.move_type = "roll"
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
                elif sonic.state.startswith("roll_"):
                    sonic.move_type = "roll"
                elif sonic.state == "crouch":
                    sonic.move_type = "roll"
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
            
    if sonic.life <= 0:
        screen.blit(text_surface, text_rect)
        screen.blit(restart_surface, restart_rect)
    else:

        # Update clock time in seconds and minutes
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) // 1000   

        minutes = elapsed_time // 60
        seconds = elapsed_time % 60     

        # If instructions are shown, freeze game state (do not update physics/animations)
        if not show_instructions:
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
            

        # Only animate when not showing instructions
        if not show_instructions:
            sonic.animation()

        # Camera behavior: compute camera offsets before drawing so we use
        # the correctly clamped camera_x and camera_y when blitting layers.
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
        effective_level_height = max(level_height, ground_level)
        max_camera_y = max(0, effective_level_height - SCREEN_HEIGHT)
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

        # Clear screen and draw background and tilemap with camera offset so they scroll
        screen.fill((0, 146, 255))
        if background_img:
            screen.blit(background_img, (-int(camera_x), -int(camera_y)))
        if 'tilemap' in globals() and getattr(tilemap, 'map_surface', None) is not None:
            try:
                blit_x = int(getattr(tilemap, 'map_origin_x', 0) - camera_x)
                blit_y = int(getattr(tilemap, 'map_origin_y', 0) - camera_y)
            except Exception:
                blit_x = -int(camera_x)
                blit_y = -int(camera_y)
            screen.blit(tilemap.map_surface, (blit_x, blit_y))

        # Convert world coordinates to screen coordinates using camera_x and camera_y
        sonic_screen_x = int(sonic.x - camera_x)
        sonic_screen_y = int(sonic.y - camera_y)
        sonic.draw(screen, (sonic_screen_x, sonic_screen_y))
        for enemy in enemies:
            enemy_screen_x = int(enemy.x - camera_x)
            enemy_screen_y = int(enemy.y - camera_y)
            # Move enemies/bullets only if not showing instructions
            bullet = None
            if not show_instructions:
                bullet = enemy.move(sonic)
            if bullet is not None:
                bullets.append(bullet)
            if bullets:
                # iterate over a copy so we can remove bullets safely while iterating
                for bullet in bullets[:]:
                    bullet_screen_x = int(bullet.x - camera_x)
                    if not show_instructions:
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
                sonic.score += 100
            enemy.draw(screen, (enemy_screen_x, enemy_screen_y))
        if rings:
            for ring in rings[:]:
                ring_screen_x = int(ring.x - camera_x)
                ring_screen_y = int(ring.y - camera_y)
                if not show_instructions:
                    ring.draw(screen, (ring_screen_x, ring_screen_y))
        # Display score, time, rings and lives
        word_score.draw(screen, (5, 5))
        word_score.set_dimensions()
        show_numbers(word_score, sonic.score)
        word_time.y =5 +word_score.height 
        word_time.set_state(elapsed_time)
        word_time.draw(screen, (5, word_time.y))
        word_time.set_dimensions()
        show_numbers(word_time, f"{minutes:02}:{seconds:02}")
        word_rings.set_state(sonic.rings)
        word_rings.y = 5 + word_score.height + word_time.height
        word_rings.draw(screen, (5, word_rings.y))
        word_rings.set_dimensions()
        show_numbers(word_rings, sonic.rings)

        # Draw lives box at bottom-left. Ensure dimensions are computed first.
        lives_box.y = (SCREEN_HEIGHT - lives_box.height) - 50
        lives_box.draw(screen, (5, lives_box.y))
        lives_box.set_dimensions()
        show_numbers(lives_box, sonic.life)
        



    # If instructions are active, draw a translucent dark overlay and the instructions text
    if show_instructions:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        instr_lines = Instructions.get_instructions()
        instr_font = pygame.font.SysFont(None, int(20 * scale_ratio))
        start_y = SCREEN_HEIGHT // 4
        for i, line in enumerate(instr_lines):
            text_surf = instr_font.render(line, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * int(28 * scale_ratio)))
            screen.blit(text_surf, text_rect)

        hint_surf = restart_font.render('Press I to continue', True, (200, 200, 200))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + len(instr_lines) * int(28 * scale_ratio) + 30))
        screen.blit(hint_surf, hint_rect)
        print(sonic.x)

    pygame.display.flip()
    clock.tick(FPS)