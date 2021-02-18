from pygame import color
from entities import passenger
from util.constants import LOSE_DELAY, LOSE_POINT, PASSENGER_LOSE
from util.draw import Shape
from entities.passenger import Passenger
import pygame as pg
from pygame.math import Vector2
from math import ceil, pi
from typing import Tuple
from time import time


class Station(object):

    def __init__(self, shape: Shape, location: Vector2):
        self.shape = shape
        self.location = location
        self.tracks = {}
        self.passengers: 'list[Passenger]' = []
        self.loseTime: float = 0
        self.losing = False

    def create_passenger(self, shape):
        self.passengers.append(Passenger(shape))

    def update(self, dt):

        if self.losing:
            pg.event.post(pg.event.Event(LOSE_POINT))
            self.loseTime -= dt
            if self.loseTime < 0:
                return True

        if len(self.passengers) >= PASSENGER_LOSE and not(self.losing):
            self.losing = True
            self.loseTime = LOSE_DELAY

        if len(self.passengers) < PASSENGER_LOSE:
            self.losing = False

        return False

    def draw(self, surface):
        if self.losing:
            lost = (LOSE_DELAY - self.loseTime) / LOSE_DELAY
            pg.draw.arc(surface, (120, 0, 0), (self.location.x-35, self.location.y-35, 70, 70),  (1-lost)*pi*2 + pi/2, pi/2, width=4)

        passenger_location = Vector2(self.location.x + 25, self.location.y - 18)
        for i, p in enumerate(self.passengers):
            p.draw(surface, passenger_location, i)

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

    def free_offset(self, dv: Vector2, offset: int):
        dv = (dv.x, dv.y)
        index = self.offset_to_index(offset)
        if dv in self.tracks and index < len(self.tracks[dv]):
            self.tracks[dv][index] = False

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
