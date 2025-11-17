import pygame
from sprites_code.sprite_classes import Sonic


current_sonic_state = "bored_2"

pygame.init()

screen = pygame.display.set_mode((800, 600))

sprite_sheet = pygame.image.load('resources\\sonic_sprites.png').convert_alpha()
sprite_sheet.set_colorkey((67, 153, 49))





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

    screen.fill((0, 0, 0))
    sonic = Sonic(2)
    sonic.draw(screen, (100, 100))
    sonic.set_state("pipe_cling_1")
    sonic.draw(screen, (300, 100))
    sonic.set_state("roll_1")
    sonic.draw(screen, (500, 100))


    pygame.display.flip()