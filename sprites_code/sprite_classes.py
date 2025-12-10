import pygame

from sprites_code.sprite_manager import get_sprite_data, get_all_sprites_of_type
from helpers.displays import screen, SCREEN_WIDTH, SCREEN_HEIGHT




class sprite(pygame.sprite.Sprite):
    def __init__(self,ratio, state=None):
        super().__init__()
        self.name = None
        self.x = 0
        self.y = 200
        self.width = 0
        self.height = 0
        self.ratio = ratio
        self.state = state
        self.img = None
        self.rect = None
        self.x_change = 0
        self.y_change = 0
        self.speed_x_subpixels = 0
        self.speed_y_subpixels = 0
        self.speed = 0
        self.move_type = None
        self.frame = 0
        self.animation_cooldown = 10
        self.last_update = 0
        self.direction = "right"
        self.sprite_sheet = None
        self.GROUND_LEVEL = 200
        self.GRAVITY = 0.5
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
        image.blit(self.sprite_sheet, (0, 0), (sx, sy, self.width, self.height))
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
    
    def collision(self):
        # Vertical movement (gravity always applies)
        self.speed_y += self.GRAVITY
        self.y += self.speed_y
        
        # Ground collision
        if self.y >= self.GROUND_LEVEL:
            self.y = self.GROUND_LEVEL
            self.speed_y = 0
            self.is_jumping = False
        # Use level/world width if provided, otherwise fall back to screen width
        try:
            from sprites_code import sprite_classes as sc
            LEVEL_WIDTH_LOCAL = getattr(sc, 'LEVEL_WIDTH', None)
        except Exception:
            LEVEL_WIDTH_LOCAL = None

        if LEVEL_WIDTH_LOCAL is not None:
            max_x = LEVEL_WIDTH_LOCAL - (self.width * self.ratio)
        else:
            max_x = SCREEN_WIDTH - (self.width * self.ratio)

        if self.x >= max_x:
            self.x = max_x
            return True
        elif self.x < 0:
            self.x = 0
            return True
        return False
    
    def get_states(self):
        states = []
        for image in get_sprite_data(f"{self.name}"):
            states.append(image.state)
        return states

    def set_state(self):
        pass

    def animation(self, frame_ms=None):
        now = pygame.time.get_ticks()
        if frame_ms is None:
            frame_ms = self.animation_cooldown

        type_key = self.move_type if self.move_type is not None else (self.state or 'idle')
        images = get_all_sprites_of_type(self.name, type_key)
        if len(images) == 0:
            return

        if now - self.last_update < frame_ms:
            return

        self.frame = (self.frame + 1) % len(images)
        try:
            self.set_state(images[self.frame])
        except Exception:
            pass

        self.last_update = now

# Level/world width in pixels. Set from main when a level is loaded.
LEVEL_WIDTH = None

def set_level_width(w):
    """Set the world width (in pixels) so sprites can use world bounds for collisions.

    Call this from `main.py` after loading the background/tilemap: `set_level_width(bg_width)`.
    """
    global LEVEL_WIDTH
    LEVEL_WIDTH = w


class Sonic(sprite):
    def __init__(self,ratio,state="idle"):
        super().__init__(ratio, state)
        self.name = "sonic"
        self.life = 3
        self.ANIM_FPS = 60
        self.SUBIMAGE_FRAMES = 24
        self.PER_SUBIMAGE_MS = int(self.SUBIMAGE_FRAMES * 1000 / self.ANIM_FPS)  # 400 ms
        self.BASE_WAIT_SUBIMAGES = 12  # 12 subimages * 24 frames = 288 frames
        self.BASE_WAIT_MS = self.BASE_WAIT_SUBIMAGES * self.PER_SUBIMAGE_MS      # 4800 ms
        self.EYES_SUBIMAGES = 3  # 72 frames = 3 * 24
        self.EYES_MS = self.EYES_SUBIMAGES * self.PER_SUBIMAGE_MS               # 1200 ms
        self.idle_start_time = None
        # maximum running speed (pixels) used to scale animation speed
        self.MAX_SPEED = 6
        # Jump mechanics
        self.is_jumping = False
        self.JUMP_POWER = -12
        self.speed_y = 0
        self.sprite_sheet = pygame.image.load('resources\\sonic_sprites.png').convert_alpha()
        self.sprite_sheet.set_colorkey((67, 153, 49))

    def set_state(self, new_state):
        self.state = new_state

    def jump(self):
        if not self.is_jumping and self.y >= self.GROUND_LEVEL:
            self.is_jumping = True
            self.speed_y = self.JUMP_POWER
            self.move_type = "roll"
            self.frame = 0

    def waiting(self):
        now = pygame.time.get_ticks()

        # Only run when Sonic is idle
        if not (self.move_type is None and self.state == "idle"):
            return

        if self.idle_start_time is None:
            self.idle_start_time = now

        t = now - self.idle_start_time

        # Phase 1: initial hold (BASE_WAIT_MS)
        if t < self.BASE_WAIT_MS:
            # remain in idle state
            self.move_type = 'idle'
            self.set_state('idle')
            self.frame = 0
            return

        # Phase 2: brief waiting subimage (1 subimage)
        if t < self.BASE_WAIT_MS + self.PER_SUBIMAGE_MS:
            self.move_type = 'idle'
            self.set_state('bored_1')
            return

        # Phase 3: eyes wide open
        if t < self.BASE_WAIT_MS + self.PER_SUBIMAGE_MS + self.EYES_MS:
            self.move_type = 'idle'
            self.set_state('bored_2')
            return

        # Phase 4+: tapping — switch to impatient/tapping move_type
        self.move_type = 'impatient'
        # let generic animation() cycle impatient frames
    def animation(self):
        # update idle-phase state machine first
        self.waiting()

        now = pygame.time.get_ticks()

        # choose lookup key: prefer state for idle phases, else move_type
        if self.state in ('idle', 'bored_1', 'bored_2'):
            type_key = self.state
        else:
            type_key = self.move_type if self.move_type is not None else (self.state or 'idle')

        images = get_all_sprites_of_type(self.name, type_key)
        if len(images) == 0:
            return

        # determine frame_ms: idle phases use PER_SUBIMAGE_MS, movement scales with speed
        if type_key in ('idle', 'bored_1', 'bored_2'):
            frame_ms = self.PER_SUBIMAGE_MS
        else:
            min_ms = 80
            if self.MAX_SPEED > 0:
                speed_ratio = min(abs(self.speed) / float(self.MAX_SPEED), 1.0)
                frame_ms = int(self.PER_SUBIMAGE_MS - speed_ratio * (self.PER_SUBIMAGE_MS - min_ms))
            else:
                frame_ms = self.PER_SUBIMAGE_MS

        if now - self.last_update < frame_ms:
            return

        prev_frame = self.frame

        # advance frame and set corresponding state
        self.frame = (self.frame + 1) % len(images)
        try:
            self.set_state(images[self.frame])
        except Exception:
            pass

        self.last_update = now

    def enemy_collision(self, enemy, sonic_screen_x, enemy_screen_x):
        try:
            self.rect = pygame.Rect(sonic_screen_x, int(self.y), int(self.width * self.ratio), int(self.height * self.ratio))
            enemy.rect = pygame.Rect(enemy_screen_x, int(enemy.y), int(enemy.width * enemy.ratio), int(enemy.height * enemy.ratio))
        except Exception:
            # If width/height not available yet, skip collision this frame
            self.rect = None
            enemy.rect = None

        if self.rect is not None and enemy.rect is not None and self.rect.colliderect(enemy.rect):
            now = pygame.time.get_ticks()
            # If Sonic is rolling (states like roll_1 .. roll_5), ignore damage
            if not (isinstance(self.state, str) and self.state.startswith("roll_")):
                if now >= getattr(self, 'invulnerable_until', 0):
                    self.life -= 1
                    self.invulnerable_until = now + 1000  # 1 second invulnerability
                    
                    # Bounce back: determine direction and apply knockback
                    if enemy.x < self.x:
                        # Enemy is to the left, bounce Sonic right
                        self.speed = 6
                        self.direction = "right"
                    else:
                        # Enemy is to the right, bounce Sonic left
                        self.speed = -6
                        self.direction = "left"
                    
                    # Reset animation state to reflect the bounce
                    self.move_type = "walk"
                    self.frame = 0
                    print(f"Sonic hit by MotoBug! Lives left: {self.life}")
            else:
                return enemy


    def move(self):
        MAX_SPEED = 6

        self.speed_x_subpixels += self.x_change

        # Convert accumulated subpixels into whole-pixel speed changes
        while self.speed_x_subpixels >= 256:
            self.speed += 1
            self.speed_x_subpixels -= 256

        while self.speed_x_subpixels <= -256:
            self.speed -= 1
            self.speed_x_subpixels += 256

        # Set speed to 0 if we get close to avoid glitches 
        if self.speed == 0 and abs(self.speed_x_subpixels) < 1:
            self.speed_x_subpixels = 0

        # Set to never go over max speed
        if self.speed > MAX_SPEED:
            self.speed = MAX_SPEED

        if self.speed < -MAX_SPEED:
            self.speed = -MAX_SPEED

        # set directions 
        if self.speed < 0:
            self.direction = "left"
        elif self.speed > 0:
            self.direction = "right"

        self.x += self.speed
        
        # Wall Collision
        collide = self.collision()
        if collide:
            self.move_type = "push"
        # Skid logic
        if self.move_type == "skid":
            if self.x_change != 0:
                if (self.speed < 0 and self.x_change < 0):
                    if abs(self.speed) >= 1:
                        self.move_type = "walk"
                        self.frame = 0
                        self.x_change = -12
                elif (self.speed > 0 and self.x_change > 0):
                    if abs(self.speed) >= 1:
                        self.move_type = "walk"
                        self.frame = 0
                        self.x_change = 12


        # Animation update
        images = get_all_sprites_of_type(self.name, self.move_type)
        if self.frame >= len(images):
            self.frame = 0
        self.set_state(images[self.frame])

class MotoBug(sprite):
    def __init__(self,ratio,start, state="bug_1"):
        super().__init__(ratio, state)
        self.name = "moto_bug"
        self.sprite_sheet = pygame.image.load('resources\\enemies.gif').convert_alpha()
        self.sprite_sheet.set_colorkey((255, 0, 255))
        self.change = 2
        self.RANGE = 300
        self.start = start
        self.x = start

    def move(self, sonic):
        # Move left/right based on current direction.
        if self.direction == "left":
            self.x += self.change
        else:
            self.x -= self.change

        # Flip direction if we've moved beyond patrol bounds
        if abs(sonic.x - self.x) < 100:
            if sonic.x < self.x:
                self.direction = "right"
                self.x -= self.change
            else:
                self.direction = "left"
                self.x += self.change
        elif self.x <= (self.start - self.RANGE):
            self.x = self.start - self.RANGE
            self.direction = "left"
        elif self.x >= (self.start + self.RANGE):
            self.x = self.start + self.RANGE
            self.direction = "right"

         

class Bomber(sprite):
    def __init__(self,x,y,ratio,state="attack_2"):
        super().__init__(ratio, state)
        self.name = "buzz_bomber"
        self.sprite_sheet = pygame.image.load('resources\\enemies.gif').convert_alpha()
        self.sprite_sheet.set_colorkey((255, 0, 255))
        self.x = x
        self.y = y

    def move(self, sonic):
        if abs(sonic.x - self.x) < 300:
            if sonic.x < self.x:
                self.direction = "left"
            else:
                self.direction = "right"
            


class GreenNewtron(sprite):
    def __init__(self,ratio,state="green_newtron_1"):
        super().__init__(ratio, state)
        self.name = "green_newtron"
        self.sprite_sheet = pygame.image.load('resources\\enemies.gif').convert_alpha()
        self.sprite_sheet.set_colorkey((255, 0, 255))
        self.x = 600
        self.y = 200

    def attack(self, sonic):
        if abs(sonic.x - self.x) < 200:
            self.state = "attack_2"

    def move(self, sonic):
        self.attack(sonic)
            
            



class BlueNewtron(sprite):
    def __init__(self,ratio,state="blue_newtron_1"):
        super().__init__(ratio, state)
        self.name = "blue_newtron"
        self.sprite_sheet = pygame.image.load('resources\\enemies.gif').convert_alpha()
        self.sprite_sheet.set_colorkey((255, 0, 255))
        self.x = 1000
        self.y = 200

    def move(self, sonic):
        pass

class Chopper(sprite):
    def __init__(self,ratio,state="chopper_1"):
        super().__init__(ratio, state)
        self.name = "chopper"
        self.sprite_sheet = pygame.image.load('resources\\enemies.gif').convert_alpha()
        self.sprite_sheet.set_colorkey((255, 0, 255))
        self.x = 1200
        self.y = 100
        
    def move(self, sonic):
        pass

class Crabmeat(sprite):
    def __init__(self,ratio,state="crabmeat_1"):
        super().__init__(ratio, state)
        self.name = "crabmeat"
        self.sprite_sheet = pygame.image.load('resources\\enemies.gif').convert_alpha()
        self.sprite_sheet.set_colorkey((255, 0, 255))
        self.x = 1400
        self.y = 200

    def move(self, sonic):
        pass