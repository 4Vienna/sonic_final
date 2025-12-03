import pygame

from sprites_code.sprite_manager import get_sprite_data, get_all_sprites_of_type
from helpers.displays import screen, SCREEN_WIDTH, SCREEN_HEIGHT

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
    
    def collision(self):
        #wall collision
        if self.x >= (SCREEN_WIDTH - self.width * self.ratio):
            self.x = SCREEN_WIDTH - (self.width * self.ratio)
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


class Sonic(sprite):
    def __init__(self,ratio,state="idle"):
        super().__init__(ratio, state)
        self.name = "sonic"
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
        self.GRAVITY = 0.5
        self.JUMP_POWER = -12
        self.GROUND_LEVEL = 200  # y position when on ground
        self.speed_y = 0

    def set_state(self, new_state):
        self.state = new_state

    def jump(self):
        """Make Sonic jump if he's on the ground"""
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
        
        # Vertical movement (gravity and jumping)
        if self.is_jumping or self.y < self.GROUND_LEVEL:
            self.speed_y += self.GRAVITY
            self.y += self.speed_y
            
            # Check if we've hit the ground
            if self.y >= self.GROUND_LEVEL:
                self.y = self.GROUND_LEVEL
                self.speed_y = 0
                self.is_jumping = False
                if self.move_type == "jump":
                    self.move_type = "walk" if self.speed != 0 else None
        
        # Wall Collision
        collide = self.collision()
        if collide:
            self.move_type = "push"

        # If we're currently skidding, only stop skidding once the
        # character has actually started running the new direction.
        # Use the sign of `change` (player input) to infer intended
        # direction; require speed to have the same sign and be
        # non-zero before switching to 'walk'. This preserves the
        # skid animation until Sonic truly reverses.
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