import math

import pygame
from pygame import font

import src.config.game_config as gc


### MAIN RESPONSIBILITY: THOMAS AAMAND WITTING S184192 ###
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def from_point(cls, point):
        return cls(point.x, point.y)

    def distance_sq(self, other: 'Point'):
        delta_x = self.x - other.x
        delta_y = self.y - other.y
        return delta_x * delta_x + delta_y * delta_y

    def distance(self, other: 'Point'):
        return math.sqrt(self.distance_sq(other))

    def __neg__(self):
        return Point(-self.x, -self.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def __str__(self):
        return "Point(%s,%s)" % (self.x, self.y)

    def scalar(self, s):
        return Point(self.x * s, self.y * s)

    def dot_product(self, other: 'Point'):
        return self.x * other.x + self.y * other.y

    def pos(self):
        return self.x, self.y

    def length(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def abs(self):
        return Point(abs(self.x), abs(self.y))

    # Rotates the vector 90 degrees anticlockwise
    def rotate_anticlock(self):
        return Point(self.y, -self.x)

    # Returns a new Point with length = 1
    def normalized(self):
        if self.length() == 0:
            return self.scalar(1)
        return self.scalar(1 / self.length())

    # Normalize in place
    def normalized_ip(self):
        tmp = self.normalized()
        self.x = tmp.x
        self.y = tmp.y

    def equals(self, point: 'Point'):
        if (self.x == point.x) and (self.y == point.y):
            return True
        else:
            return False


class GraphicsPoint(Point):
    __lastId = 0

    def __init__(self, x, y, index=True, paths=None):
        super().__init__(x, y)

        if index:
            self.index = GraphicsPoint.__lastId
            GraphicsPoint.__lastId += 1
        # else:
        #     self.index = -1

        if paths is None:
            paths = []

        self.paths = paths
        self.radius = 9
        self.color = gc.POINT_COLOR
        self.regions = set()
        self.num_paths = len(paths)

        # Draw circle on own surface
        self.image = pygame.Surface([self.radius * 2, self.radius * 2])
        self.image.fill(gc.WHITE)

        # All white is considered to be transparent
        self.image.set_colorkey(gc.WHITE)

        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)

        self.rect = self.image.get_rect()
        self.update_rect()

    @classmethod
    def from_point(cls, point, index=True):
        return cls(point.x, point.y, index)

    @staticmethod
    def setLastID(index: int):
        GraphicsPoint.__lastId = index

    def available(self):
        return len(self.paths) < 3

    def add_to_path(self, path):
        self.paths.append(path)
        self.num_paths = len(self.paths)
        if self.num_paths >= 3:
            self.update_color(gc.POINT_COLOR_UNAVAILABLE)

    def update_rect(self):
        self.rect.x = self.x - self.radius
        self.rect.y = self.y - self.radius

    def update_color(self, color):
        self.color = color
        self.image.fill(gc.WHITE)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)

        self.rect = self.image.get_rect()
        self.update_rect()

    def draw(self, surf):
        surf.blit(self.image, self.rect)
        font = pygame.font.Font(pygame.font.get_default_font(), 16)

        if hasattr(self, 'index'):
            text_surface = font.render(str(self.index), True, (0, 0, 0))
            surf.blit(text_surface, self.pos())

    def update_radius(self, radius):
        self.radius = radius
        self.image.fill(gc.WHITE)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), radius)

        self.rect = self.image.get_rect()
        self.update_rect()
    def __str__(self):
        return "GraphicsPoint(%s,%s), id: %d" % (self.x, self.y, self.index)
