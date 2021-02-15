from util.draw import Shape
from entities.passenger import Passenger
import pygame as pg
from pygame.math import Vector2
from math import ceil
from typing import Tuple
import time


class Station(object):

    def __init__(self, shape: Shape, location: Vector2):
        self.shape = shape
        self.location = location
        self.tracks = {}
        self.passengers: Passenger = []
        self.loseTime = time.time()
        self.losing = False

    def create_passenger(self, shape):
        self.passengers.append(Passenger(shape))

    def update(self):
        for p in self.passengers:
            p.update()

        if(self.losing):
            if((int(time.time()-int(self.loseTime))) > 10):
                return True

        if(len(self.passengers) >= 6 and not(self.losing)):
            self.losing = True
            self.loseTime = time.time()

        if (len(self.passengers) < 6):
            self.losing = False

    def draw(self, surface):
        for i, p in enumerate(self.passengers):
            p.draw(surface, self.location, i)

        self.shape.draw(surface, self.location, 40, True, 4)

    def contains(self, pt: Tuple[int, int]):
        return (self.location.x-pt[0]) ** 2 + (self.location.y-pt[1]) ** 2 < 625

    def track_offset(self, dv: Vector2, set: bool):
        _dv = (dv.x, dv.y)
        if _dv not in self.tracks:
            index = 0
        elif False in self.tracks[_dv]:
            index = self.tracks[_dv].index(False)
        else:
            index = len(self.tracks[_dv])

        offset = Station.index_to_offset(index)
        if set:
            self.use_offset(dv, offset)
        return offset

    def use_offset(self, dv: Vector2, offset: int):
        dv = (dv.x, dv.y)
        # turn the offset back to an index
        index = self.offset_to_index(offset)

        # make sure the offset list is large enough
        if dv not in self.tracks:
            self.tracks[dv] = [False for _ in range(index+1)]
        else:
            while len(self.tracks[dv]) < index+1:
                self.tracks[dv].append(False)

        # mark the offset as used
        self.tracks[dv][index] = True

    def can_use_offset(self, dv: Vector2, offset):
        dv = (dv.x, dv.y)
        index = self.offset_to_index(offset)
        return not(dv in self.tracks and
                   len(self.tracks[dv]) > index and
                   self.tracks[dv][index])

    @classmethod
    def next_offset(cls, offset: int):
        return Station.index_to_offset(Station.offset_to_index(offset)+1)

    @classmethod
    def offset_to_index(cls, offset: int):
        index = offset * 2
        if index < 0:
            index = abs(index)
        elif index > 0:
            index -= 1
        return index

    @classmethod
    def index_to_offset(cls, index: int):
        return ceil(index / 2) * (-1 if index % 2 == 0 else 1)
