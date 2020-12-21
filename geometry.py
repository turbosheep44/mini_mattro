from pygame.math import Vector2
from math import sqrt
from typing import Tuple


class Pt(object):

    def __init__(self, pt: tuple):
        self.x = pt[0]
        self.y = pt[1]

    def __add__(self, other: Vector2):
        return Pt((self.x + other.x, self.y + other.y))

    def __str__(self):
        return f"({self.x}, {self.y})"

    def distance_to(self, other: Tuple[int, int]):
        return sqrt((self.x - other[0]) ** 2 + (self.y - other[1])**2)

    def as_tuple(self):
        return (self.x, self.y)

    def vector_to(self, other: 'Pt'):
        return Vector2(other.x - self.x, other.y - self.y)

    def clone(self) -> 'Pt':
        return Pt(self.as_tuple())
