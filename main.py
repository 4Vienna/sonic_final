import pygame
from sprites_code.sprite_classes import Sonic
from helpers.displays import screen, SCREEN_WIDTH, SCREEN_HEIGHT

pygame.init()



sprite_sheet = pygame.image.load('resources\\sonic_sprites.png').convert_alpha()
sprite_sheet.set_colorkey((67, 153, 49))
sonic = Sonic(2)
player_move = False


last_update = pygame.time.get_ticks()


def get_sprite_image(x, y, width, height, colorkey=None):
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    image.blit(sprite_sheet, (0, 0), (x, y, width, height))
    if colorkey is not None:
        image.set_colorkey(colorkey)
    return image

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
        


    sonic.animation()
    text_surface = text_set.render(f"Sonic position: {sonic.x} direction: {sonic.direction} speed: {sonic.speed} change: {sonic.x_change} state: {sonic.move_type} frame: {sonic.frame}", True, (255,255,255))
    text_rect = text_surface.get_rect(topleft=(0, 0))
    screen.fill((0, 0, 0))
    sonic.draw(screen, (sonic.x, sonic.y))
    screen.blit(text_surface, text_rect)

    pygame.display.flip()
    clock.tick(FPS)