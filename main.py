import pygame
from sprites_code.sprite_classes import Sonic

pygame.init()

screen = pygame.display.set_mode((800, 600))

sprite_sheet = pygame.image.load('resources\\sonic_sprites.png').convert_alpha()
sprite_sheet.set_colorkey((67, 153, 49))
sonic = Sonic(2)
player_move = False




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
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_d:
                player_move = False
            

    if player_move:
        sonic.move_type = "walk"
        sonic.change = 2
        sonic.move()
    else:
        if sonic.speed > 0:
            sonic.change = -.2
            sonic.run()
        else:
            sonic.change = 0
            sonic.set_state("idle")



    screen.fill((0, 0, 0))
    sonic.draw(screen, (sonic.x, sonic.y))


    pygame.display.flip()