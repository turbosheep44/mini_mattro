import pygame as pg
from pygame import Vector2


# events
SELECT_TRACK = pg.USEREVENT + 1
SCORE_POINT = pg.USEREVENT + 2

# layout
TOP = "top"
BOTTOM = "bottom"
RIGHT = "right"
LEFT = "left"
MIDDLE = "middle"

CARDINALS = [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0),
             Vector2(1, -1), Vector2(1, 1), Vector2(-1, -1),  Vector2(-1, 1)]
COLORS = [(125, 0, 0), (0, 125, 0), (0, 0, 125), (125, 125, 0), (125, 0, 125), (0, 125, 125), (125, 125, 125),
          (125, 0, 125), (125, 125, 0), (0, 125, 125)]

# game speed
TRAIN_SPEED = 70
