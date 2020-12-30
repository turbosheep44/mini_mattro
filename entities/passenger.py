from util.draw import Shape
import pygame as pg
from pygame import Vector2


class Passenger(object):

    def __init__(self, shape: Shape):
        self.shape = shape

    def draw(self, surface, location, offset):
        location = Vector2(location.x + 25 + ((15 * offset)), location.y - 18)
        self.shape.draw(surface, location, 15, True)

    def should_embark(self) -> bool:
        return True

    def should_disembark(self) -> bool:
        return True
