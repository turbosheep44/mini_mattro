import pygame as pg
from pygame.math import Vector2
from math import ceil
from typing import Tuple


class Station(object):
    SQUARE, CIRCLE, TRIANGLE = "square", "circle", "triangle"

    def __init__(self, shape, location: Vector2):
        self.shape = shape
        self.location = location
        self.tracks = {}

    def draw(self, surface):
        # SQUARE
        if self.shape == Station.SQUARE:
            pg.draw.rect(surface, (180, 180, 180), pg.Rect(self.location.x-20, self.location.y-20, 40, 40))
            pg.draw.rect(surface, (0, 0, 0), pg.Rect(self.location.x-20, self.location.y-20, 40, 40), 5)

        # CIRCLE
        elif self.shape == Station.CIRCLE:
            pg.draw.circle(surface, (180, 180, 180), self.location, 25)
            pg.draw.circle(surface, (0, 0, 0), self.location, 25, 5)

        # TRIANGLE
        elif self.shape == Station.TRIANGLE:
            pg.draw.polygon(surface, (180, 180, 180),
                            [[self.location.x, self.location.y - 25],
                             [self.location.x + 25, self.location.y+17],
                             [self.location.x - 25, self.location.y+17]])
            pg.draw.polygon(surface, (0, 0, 0),
                            [[self.location.x, self.location.y - 25],
                             [self.location.x + 25, self.location.y+17],
                             [self.location.x - 25, self.location.y+17]], 5)

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
