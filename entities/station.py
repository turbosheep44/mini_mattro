import pygame as pg
from pygame.math import Vector2
from math import ceil
from util.geometry import Pt


class Station(object):
    SQUARE, CIRCLE, TRIANGLE = "square", "circle", "triangle"

    def __init__(self, shape, location: Pt):
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
            pg.draw.circle(surface, (180, 180, 180), self.location.as_tuple(), 25)
            pg.draw.circle(surface, (0, 0, 0), self.location.as_tuple(), 25, 5)

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

    def contains(self, pt: Pt):
        return (self.location.x-pt.x) ** 2 + (self.location.y-pt.y) ** 2 < 625

    def track_offset(self, direction: Vector2, set: bool):
        dv = (direction.x, direction.y)

        if dv not in self.tracks:
            if set:
                self.tracks[dv] = [True]
            return 0

        if False in self.tracks[dv]:
            index = self.tracks[dv].index(False)
            if set:
                self.tracks[dv][index] = True
        else:
            index = len(self.tracks[dv])
            if set:
                self.tracks[dv].append(True)

        return Station.index_to_offset(index)

    def use_offset(self, direction: Vector2, offset: int):
        # turn the offset back to an index
        index = self.offset_to_index(offset)

        dv = (direction.x, direction.y)

        # make sure the offset list is large enough
        if dv not in self.tracks:
            self.tracks[dv] = [False for _ in range(index+1)]
        else:
            while len(self.tracks[dv]) < index+1:
                self.tracks[dv].append(False)

        self.tracks[dv][index] = True

    def can_use_offset(self, direction, offset):
        dv = (direction.x, direction.y)
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
