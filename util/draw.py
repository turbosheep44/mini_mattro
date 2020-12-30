import pygame as pg
from pygame import Vector2


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
