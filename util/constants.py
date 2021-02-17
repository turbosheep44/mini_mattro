import pygame as pg
from pygame import Vector2
from typing import List


# events
SELECT_TRACK = pg.USEREVENT + 1
SCORE_POINT = pg.USEREVENT + 2
TRAIN_STOP = pg.USEREVENT + 3
LOSE_POINT = pg.USEREVENT + 4
REQUEST_TRAIN = pg.USEREVENT + 5
UPGRADE_TRAIN = pg.USEREVENT + 6
EOL_TRAIN = pg.USEREVENT + 7
TRAINS_CHANGED = pg.USEREVENT + 8

# layout
TOP = "top"
BOTTOM = "bottom"
RIGHT = "right"
LEFT = "left"
MIDDLE = "middle"

# layers
RAIL_LAYER = 0
REMOVED_RAIL_LAYER = 1
TRAIN_LAYER = 2
STATION_LAYER = 3
GUI_LAYER = 4

CARDINALS: List[Vector2] = [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0),
                            Vector2(1, -1), Vector2(1, 1), Vector2(-1, -1),  Vector2(-1, 1)]
COLORS = [(125, 0, 0), (0, 125, 0), (0, 0, 125), (125, 125, 0), (125, 0, 125), (0, 125, 125), (125, 125, 125),
          (125, 0, 125), (125, 125, 0), (0, 125, 125)]

# game speed
TRAIN_SPEED = 70
TRAIN_SECONDS_PER_ACTION = 0.4


TRAIN_CAPACITY = 6
PASSENGER_LOSE = 60
LOSE_DELAY = 10
