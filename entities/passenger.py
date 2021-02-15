from util.draw import Shape
import pygame as pg
from pygame import Vector2
import time
from util.constants import LOSE_POINT


class Passenger(object):

    def __init__(self, shape: Shape):
        self.shape = shape
        self.startTime = time.time()
        self.penalised = False

    def draw(self, surface, location, offset):
        location = Vector2(location.x + 25 + ((15 * offset)), location.y - 18)
        self.shape.draw(surface, location, 15, True)

    def should_embark(self) -> bool:
        return True

    def should_disembark(self, shape) -> bool:
        if self.shape == shape:
            return True
        else:
            return False

    def update(self):

        if(((int(time.time())-int(self.startTime)) > 5)and not self.penalised):
            self.penalised = True
            self.startTime = time.time()
            pg.event.post(pg.event.Event(LOSE_POINT))

        if(((int(time.time())-int(self.startTime)) > 5)and self.penalised):
            self.penalised = False
