import pygame
from sprites_code.sprite_classes import Sonic

pygame.init()

screen = pygame.display.set_mode((640, 448))

sprite_sheet = pygame.image.load('resources\\sonic_sprites.png').convert_alpha()
sprite_sheet.set_colorkey((67, 153, 49))
sonic = Sonic(2)
player_move = False
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()

last_update = pygame.time.get_ticks()


def get_sprite_image(x, y, width, height, colorkey=None):
    image = pygame.Surface((width, height), pygame.SRCALPHA)
    image.blit(sprite_sheet, (0, 0), (x, y, width, height))
    if colorkey is not None:
        image.set_colorkey(colorkey)
    return image

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
                sonic.change = 12
                if sonic.speed >= 0:
                    sonic.direction = "right"
            if keys[pygame.K_a]:
                player_move = True
                sonic.change = -12
                if sonic.direction == "right":
                    sonic.move_type = "skid"
                if sonic.speed <= 0:
                    sonic.direction = "left"
                    
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d:
                player_move = False
                if sonic.change == 0:
                    sonic.change = -128
                else:
                    sonic.change = -abs(sonic.change)
            if event.key == pygame.K_a:
                player_move = False
                if sonic.change == 0:
                    sonic.change = 128
                else:
                    sonic.change = abs(sonic.change)
            

    if player_move:
        current_time = pygame.time.get_ticks()
        if current_time - last_update >= sonic.animation_cooldown:
            sonic.frame += 1
            last_update = current_time
        if sonic.move_type == "skid":
            if (sonic.direction == "right" and sonic.speed < 0) or (sonic.direction == "left" and sonic.speed > 0):
                sonic.move_type = "skid"
            else:
                sonic.move_type = "walk"
        else:
            sonic.move_type = "walk"
        sonic.move(SCREEN_WIDTH)
        
    else:
        if (sonic.speed > 0 and sonic.direction == "right") or (sonic.speed < 0 and sonic.direction == "left"):
            current_time = pygame.time.get_ticks()
            if current_time - last_update >= sonic.animation_cooldown:
                sonic.frame += 1
                last_update = current_time
            sonic.move_type = "walk"
            sonic.move(SCREEN_WIDTH)
        else:
            sonic.change = 0
            sonic.frame = 99
            sonic.set_state("idle")



    screen.fill((0, 0, 0))
    sonic.draw(screen, (sonic.x, sonic.y))

    pygame.display.flip()