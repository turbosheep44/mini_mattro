from util.draw import Shape
import pygame as pg
from pygame import Vector2
from time import time
from util.constants import LOSE_POINT


class Passenger(object):

    def __init__(self, shape: Shape):
        self.shape = shape
        self.is_boarding: bool = False

    def draw(self, surface, location, offset):
        location = Vector2(location.x + (15 * offset), location.y)
        self.shape.draw(surface, location, 15, True)

    def should_embark(self) -> bool:
        return True

    def should_disembark(self, shape) -> bool:
        if self.shape == shape:
            return True
        else:
            return False
