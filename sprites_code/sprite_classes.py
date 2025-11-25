import pygame

from sprites_code.sprite_manager import get_sprite_data, get_all_sprites_of_type

screen = pygame.display.set_mode((640, 448))

sprite_sheet = pygame.image.load('resources\\sonic_sprites.png').convert_alpha()
sprite_sheet.set_colorkey((67, 153, 49))

class sprite():
    def __init__(self,ratio, state=None):
        self.name = None
        self.x = 0
        self.y = 200
        self.width = 0
        self.height = 0
        self.ratio = ratio
        self.state = state
        self.img = None
        self.change = 0
        self.speed_subpixels = 0
        self.speed = 0
        self.move_type = None
        self.frame = 0
        self.animation_cooldown = 10
        self.direction = "right"

    def set_data(self):
        if self.state is not None and self.name is not None:
            data = get_sprite_data(f"{self.name}_{self.state}")
            if data is not None:
                (self.src_x, self.src_y, self.width, self.height) = data
            else:
                self.src_x, self.src_y, self.width, self.height = 0, 0, 0, 0

    def set_image(self, colorkey=None):
        image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        sx = getattr(self, 'src_x', 0)
        sy = getattr(self, 'src_y', 0)
        image.blit(sprite_sheet, (0, 0), (sx, sy, self.width, self.height))
        if colorkey is not None:
            image.set_colorkey(colorkey)
        self.img = image

    def resize_image(self):
        if self.img is not None:
            self.img = pygame.transform.scale(self.img, (self.width *self.ratio, self.height*self.ratio))

    def draw(self, surface, position):
        self.set_data()
        self.set_image()
        if self.direction == "left" and self.img is not None:
            self.img = pygame.transform.flip(self.img, True, False)
        if self.img is not None:
            self.resize_image()
            surface.blit(self.img, position)
    
    def get_states(self):
        states = []
        for image in get_sprite_data(f"{self.name}"):
            states.append(image.state)
        return states

    def set_state(self):
        pass


class Sonic(sprite):
    def __init__(self,ratio,state="idle"):
        super().__init__(ratio, state)
        self.name = "sonic"

    def set_state(self, new_state):
        self.state = new_state


    def move(self, width):
        MAX_SPEED = 6
        self.speed_subpixels += self.change
        if self.speed_subpixels >= 256:
            self.speed += self.speed_subpixels // 256
            self.speed_subpixels = self.speed_subpixels % 256
        elif self.speed_subpixels <= 0:
            self.speed += (self.speed_subpixels // 256) - 1
            self.speed_subpixels = 256 + (self.speed_subpixels % 256)
        if self.speed >= MAX_SPEED:
            self.speed = MAX_SPEED
        self.x += self.speed
        if self.x >= width:
            self.x = -self.width * self.ratio
        elif self.x < 0:
            self.x = 0
        images = get_all_sprites_of_type(self.name, self.move_type)
        if self.frame >= len(images):
            self.frame = 0
        self.set_state(images[self.frame])