import pygame
from sprites_code.sprite_classes import *
from helpers.displays import screen, SCREEN_WIDTH, SCREEN_HEIGHT
from sprites_code.build_background import TileMap

# Load background image
background_img = pygame.image.load('resources/backgrounds/green_hill_zone.png').convert_alpha()
bg_width, bg_height = background_img.get_size()
# Camera offset (world x position of left edge of screen)
camera_x = 0

# Inform sprites about the level/world width so collisions use world bounds
set_level_width(bg_width)

pygame.init()



sonic = Sonic(2)
# Player state: lives and simple invulnerability timer after being hit
sonic.invulnerable_until = 0

enemies = [GreenNewtron(2)]
bullets = []
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
    # - While Sonic is left of the screen center, keep the camera at 0 (start at edge)
    # - Once Sonic passes the center, keep him visually centered until level end
    max_camera_x = max(0, bg_width - SCREEN_WIDTH)
    half_screen = SCREEN_WIDTH // 2
    if sonic.x <= half_screen:
        camera_x = 0
    else:
        camera_x = sonic.x - half_screen
        if camera_x > max_camera_x:
            camera_x = max_camera_x

    # Draw background offset by camera
    screen.blit(background_img, (-int(camera_x), 0))
    # Draw tilemap (pre-rendered) with same camera offset so tiles scroll
    if 'tilemap' in globals() and getattr(tilemap, 'map_surface', None) is not None:
        screen.blit(tilemap.map_surface, (-int(camera_x), 0))
    text_surface = text_set.render(f"Sonic position: {sonic.x} direction: {sonic.direction} speed: {sonic.speed} change: {sonic.x_change} state: {sonic.move_type} frame: {sonic.frame}", True, (255,255,255))
    text_rect = text_surface.get_rect(topleft=(0, 0))
    
    # Convert world coordinates to screen coordinates using camera_x
    sonic_screen_x = int(sonic.x - camera_x)
    sonic.draw(screen, (sonic_screen_x, int(sonic.y)))
    for enemy in enemies:
        enemy_screen_x = int(enemy.x - camera_x)
        bullet = enemy.move(sonic)
        if bullet is not None:
            bullets.append(bullet)
        if bullets:
            for bullet in bullets:
                bullet_screen_x = int(bullet.x - camera_x)
                bullet.move()
                bullet.draw(screen, (bullet_screen_x, int(bullet.y)))
                # Check collision between Sonic and bullet
                if sonic.enemy_collision(bullet, sonic_screen_x, bullet_screen_x):
                    print("Sonic hit by bullet!")
                    bullets.remove(bullet)
                if bullet.x < 0 or bullet.x > bg_width:
                    bullets.remove(bullet)
               

        hit = sonic.enemy_collision(enemy, sonic_screen_x, enemy_screen_x)
        if hit is not None:
            # Handle enemy defeat logic here
            enemies.remove(hit)
            print(f"Enemies left: {enemies}")
            print(f"Defeated {hit.name}!")
        enemy.draw(screen, (enemy_screen_x, int(enemy.y)))

    screen.blit(text_surface, text_rect)

    pygame.display.flip()
    clock.tick(FPS)