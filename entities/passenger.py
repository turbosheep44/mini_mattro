from util.draw import Shape
import pygame as pg
from pygame import Vector2
from time import time
from util.constants import LOSE_POINT


class Passenger(object):

    def __init__(self, shape: Shape):
        self.shape = shape
        self.startTime = time()
        self.penalised = False
        self.is_boarding = False

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

    # def update(self):
    #     if time()-self.startTime > 5 and not self.penalised:
    #         self.penalised = True
    #         self.startTime = time()
    #         pg.event.post(pg.event.Event(LOSE_POINT))
    #     if time()-self.startTime > 5 and self.penalised:
    #         self.penalised = False
