from typing import List, Tuple
import pygame
import numpy as np
import math
import random

from const import ROCKET_IMAGE_PATH, UNIT_IMAGE_PATH, TARGET_IMAGE_PATH, MoveType


class Rocket(pygame.sprite.Sprite):
    cooldown = 2000

    def __init__(self, source: List[int], dest: List[int], target: pygame.sprite.Sprite):
        super(Rocket, self).__init__()
        self.image = pygame.image.load(ROCKET_IMAGE_PATH)
        self.orig_image = self.image

        self.source = source
        self.dest = dest

        self.vel_base = 10
        self.vel_x = self.vel_base
        self.vel_y = 0
        self.target = target

        # rockets starts from middle of soldier
        self.rect = self.image.get_rect(center=(source[0], source[1]))

        if isinstance(dest, Tuple):
            self.image, self.rect = self.rotate()
        elif isinstance(dest, int):
            self.image, self.rect = self.fire_angle(dest)

    def fire_angle(self, angle) -> Tuple[pygame.Surface, pygame.Rect]:
        angle %= 360
        self.angle = 360-angle

        rad = angle / 180 * math.pi
        if angle % 90 == 0:
            if angle % 180 == 0:
                self.vel_x = 0
                self.vel_y = -self.vel_base if angle == 0 else self.vel_base

            else:
                self.vel_x = self.vel_base if angle == 90 else -self.vel_base
                self.vel_y = 0

        else:
            # top right
            if angle < 90:
                self.vel_x = self.vel_base * math.sin(rad)
                self.vel_y = -self.vel_base * math.cos(rad)

            # bottom right
            elif angle < 180:
                self.vel_x = self.vel_base * math.cos(rad - math.pi/2)
                self.vel_y = self.vel_base * math.sin(rad - math.pi/2)

            # bottom left
            elif angle < 270:
                self.vel_x = -self.vel_base * math.sin(rad - math.pi)
                self.vel_y = self.vel_base * math.cos(rad - math.pi)

            # top left
            else:
                self.vel_x = -self.vel_base * math.cos(rad - 3*math.pi/2)
                self.vel_y = -self.vel_base * math.sin(rad - 3*math.pi/2)

        rot_image = pygame.transform.rotate(self.image, 360-angle)
        rot_rect = rot_image.get_rect(center=self.rect.center)
        return rot_image, rot_rect

    def dist_from_target(self) -> int:
        dx, dy = self.rect.centerx - \
            self.target.rect.centerx, self.rect.centery - self.target.rect.centery
        return int(math.sqrt(dx**2+dy**2))

    def calculate_trajectory(self) -> int:
        """Calculates x and y velocities for movement to target and returns rotation required for rocket

        Returns:
            int: rotation in degrees
        """

        dy, dx = self.dest[1]-self.source[1], self.dest[0]-self.source[0]

        # if perfect left/right, no need to calculate
        if dy == 0:
            self.vel_x = self.vel_base if dx > 0 else -self.vel_base
            self.vel_y = 0
            return 270 if dx > 0 else 90

        # if perfect up/down, no need to calculate
        if dx == 0:
            self.vel_x = 0
            self.vel_y = self.vel_base if dy > 0 else -self.vel_base
            return 180 if dy > 0 else 0

        # angle of source to dest
        theta = math.atan(abs(dy)/abs(dx))

        # positive or negative velocity depending on dy and dx
        self.vel_x = self.vel_base * math.cos(theta) * (1 if dx > 0 else -1)
        self.vel_y = self.vel_base * math.sin(theta) * (1 if dy > 0 else -1)

        # base angle of rotation, to be changed with angle of trajectory
        base_angle = 90 if dx < 0 else -90

        # returns rotation based on quadrants
        if dy < 0 and dx < 0 or dy > 0 and dx > 0:
            return base_angle - (theta * 180 / math.pi)
        else:
            return base_angle + (theta * 180 / math.pi)

    def rotate(self, angle: float = None) -> Tuple[pygame.Surface, pygame.Rect]:
        """Generates rotated image and rect based off trajectory

        Returns:
            Tuple[pygame.Surface, pygame.Rect]: Rotated image and rect
        """

        if angle == None:
            angle = self.calculate_trajectory()
            self.angle = angle
            # print(angle)
        rot_image = pygame.transform.rotate(self.image, angle)
        rot_rect = rot_image.get_rect(center=self.rect.center)
        return rot_image, rot_rect

    def rotate_abs(self, angle: float):
        self.image = pygame.transform.rotate(self.orig_image, angle)
        self.rect = self.image.get_rect(center=self.rect.center)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)

    def update(self) -> Tuple[bool, pygame.sprite.Sprite]:
        """Moves rocket and checks for collision with target

        Returns:
            Tuple[bool, pygame.sprite.Sprite]: Bool value whether rocket collided with target and the target sprite
        """

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        return pygame.sprite.collide_rect(self, self.target), self.target

    def is_out_of_bounds(self):
        return self.rect.x < 0 or self.rect.x > 800 or self.rect.y < 0 or self.rect.y > 600


class Soldier(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, flip: bool = False):
        super(Soldier, self).__init__()
        self.image = pygame.image.load(UNIT_IMAGE_PATH)
        if flip:
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.flip = flip
        self.vel = 10

    def draw(self, screen: pygame.Surface):
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 2)

    def set_target(self, target: pygame.sprite.Sprite):
        self.target = target

    def move_to_target(self, step_x: int, step_y: int):
        """Moves towards the assigned target by a step value

        Args:
            step_x (int): Amount to move in x direction
            step_y (int): Amount to move in y direction
        """

        dy = self.target.rect.centery - self.rect.centery
        dx = self.target.rect.centerx - self.rect.centerx

        if dy < 0:
            step_y *= -1
        if dx < 0:
            step_x *= -1

        self.rect.x += step_x
        self.rect.y += step_y

    def dist_from_target(self) -> float:
        """Gets distance of Soldier from its assigned target

        Returns:
            float: Distance in float
        """

        dy = self.target.rect.centery - self.rect.centery
        dx = self.target.rect.centerx - self.rect.centerx
        return math.sqrt(dy**2 + dx**2)

    def angle_from_target(self) -> float:
        """Gets angle of Soldier to its assigned target. Angle is counted clockwise

        Returns:
            float: Angle in degrees
        """

        dy = self.target.rect.centery - self.rect.centery
        dx = self.target.rect.centerx - self.rect.centerx
        return (math.atan2(dy, dx) * 180 / math.pi) + 180

    def shoot(self, dest: Tuple[int]) -> Rocket:
        """Shoots a rocket at coordinate dest

        Args:
            dest (Tuple[int]): Coordinate for rocket to move towards

        Returns:
            Rocket: Rocket object that was generated
        """

        if self.target == None:
            return

        source = [self.rect.x + self.rect.width //
                  2, self.rect.y + self.rect.height//2]

        return Rocket(source, dest, self.target)

    def shoot_angle(self, angle: int) -> Rocket:
        """Shoots rocket at an angle

        Args:
            angle (int): Angle to fire at

        Returns:
            Rocket: Rocket object that was generated
        """
        if self.target == None:
            return

        source = [self.rect.x + self.rect.width //
                  2, self.rect.y + self.rect.height//2]

        return Rocket(source, angle, self.target)

    def draw_firing_angle(self, screen: pygame.Surface, angle: int):
        """Draws a line aligned with the firing angle for debugging

        Args:
            screen (pygame.Surface): Pygame screen
            angle (int): Angle to draw the line
        """

        dest = list(self.rect.center)
        vector = pygame.math.Vector2(0, -40)
        vector.rotate_ip(angle)
        dest = np.add(dest, vector)
        pygame.draw.line(screen, (255, 0, 0), self.rect.center, dest, 2)

    def is_out_of_range(self):
        return self.rect.x < 0 or self.rect.x > 800 or self.rect.y < 0 or self.rect.y > 600

    def manual_move(self):
        keys = pygame.key.get_pressed()

        # movement for player (arrow keys)
        if not self.flip:
            if keys[pygame.K_LEFT]:
                if not ((self.rect.x - self.vel) <= 0):
                    self.rect.x -= self.vel

            if keys[pygame.K_RIGHT]:
                if not ((self.rect.x + self.vel) >= 750):
                    self.rect.x += self.vel

            if keys[pygame.K_UP]:
                if not ((self.rect.y - self.vel) <= 0):
                    self.rect.y -= self.vel

            if keys[pygame.K_DOWN]:
                if not ((self.rect.y + self.vel) >= 550):
                    self.rect.y += self.vel

        # movement for enemy (WASD keys)
        else:
            if keys[pygame.K_a]:
                self.rect.x -= self.vel

            if keys[pygame.K_d]:
                self.rect.x += self.vel

            if keys[pygame.K_w]:
                self.rect.y -= self.vel

            if keys[pygame.K_s]:
                self.rect.y += self.vel

    def ai_move(self, next_action):
        if next_action == 0:
            if not ((self.rect.x - self.vel) <= 0):
                self.rect.x -= self.vel

        elif next_action == 1:
            if not ((self.rect.x + self.vel) >= 750):
                self.rect.x += self.vel

        elif next_action == 2:
            if not ((self.rect.y - self.vel) <= 0):
                self.rect.y -= self.vel

        elif next_action == 3:
            if not ((self.rect.y + self.vel) >= 550):
                self.rect.y += self.vel

    def setpos(self, x, y):
        self.rect.x = x
        self.rect.y = y


class Target(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, move_type: int):
        super(Target, self).__init__()
        self.image = pygame.image.load(TARGET_IMAGE_PATH)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

        self.move_type = move_type
        self.vel_base = 10
        self.vel_x = 0
        self.vel_y = 0

        # randomise starting position for circling target
        self.angle = random.choice([0, 90, 180, 270])
        self.base_x = self.rect.x
        self.base_y = self.rect.y

    def move(self):
        if self.move_type == MoveType.UP_DOWN:
            self.up_down()

        if self.move_type == MoveType.ZIG_ZAG:
            self.zig_zag()

        if self.move_type == MoveType.CIRCLE:
            self.circle()

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

    def up_down(self):
        # initial movement
        if self.vel_x == 0 and self.vel_y == 0:
            self.vel_x = 0
            self.vel_y = self.vel_base

        # reverse direction when hits boundary
        if self.rect.y < 100 or self.rect.y > 500:
            self.vel_y = -self.vel_y

    def zig_zag(self):
        # initial movement
        if self.vel_x == 0 and self.vel_y == 0:
            self.vel_x = -5
            self.vel_y = 9

        # change l-r when hit boundary
        if self.rect.x < 500 or self.rect.x > 700:
            self.vel_x = - self.vel_x

        # change u-d when hit boundary
        if self.rect.y < 50 or self.rect.y > 500:
            self.vel_y = -self.vel_y

    def circle(self):
        vector = pygame.math.Vector2(250, 0)

        self.angle += 5
        vector.rotate_ip(self.angle)
        self.rect.x = self.base_x + vector[0]
        self.rect.y = self.base_y + vector[1]
