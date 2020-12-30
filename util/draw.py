import pygame as pg
from pygame import Vector2
from enum import Enum


def ortholine(surface, color, start: Vector2, end: Vector2, width=1, rounded=False):
    """
    ortholine draws a line which has constant thickness at all rotations and ends which 
    are perpendicular to the direction of the line

    the pygame line function is thinner when rotate and ends are in line with the xy axes
    """

    dv = end - start
    if not dv.x and not dv.y:
        return
    orthog_scale = (width/2) / ((dv.x ** 2) + (dv.y ** 2)) ** 0.5
    orthog = Vector2(dv.y * orthog_scale, -dv.x * orthog_scale)

    points = [
        start + orthog, start - orthog,
        end - orthog, end + orthog,
    ]

    pg.draw.polygon(surface, color, points)
    if rounded:
        pg.draw.circle(surface, color, start, width/2)
        pg.draw.circle(surface, color, end, width/2)


# shapes
class Shape(Enum):
    SQUARE = 0
    CIRCLE = 1
    TRIANGLE = 2

    def draw(self, surface, center: Vector2, diameter: int, outline: bool = False, thickness: int = 1):
        radius = diameter/2

        # SQUARE
        if self == Shape.SQUARE:
            diameter *= 0.8
            radius *= 0.8
            pg.draw.rect(surface, (180, 180, 180), pg.Rect((center.x-radius, center.y-radius), (diameter, diameter)))
            if outline:
                pg.draw.rect(surface, (0, 0, 0), pg.Rect((center.x-radius, center.y-radius), (diameter, diameter)), thickness)

        # CIRCLE
        elif self == Shape.CIRCLE:
            pg.draw.circle(surface, (180, 180, 180), center, radius)
            if outline:
                pg.draw.circle(surface, (0, 0, 0), center, radius, thickness)

        # TRIANGLE
        elif self == Shape.TRIANGLE:
            radius *= 0.75
            pg.draw.polygon(surface, (180, 180, 180),
                            [[center.x, center.y - radius],
                             [center.x + radius, center.y+radius],
                             [center.x - radius, center.y+radius]])
            if outline:
                pg.draw.polygon(surface, (0, 0, 0),
                                [[center.x, center.y - radius],
                                 [center.x + radius, center.y+radius],
                                 [center.x - radius, center.y+radius]], thickness)
