from util.constants import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from entities import Rail, TrackSegment, Station


class Data(object):
    NEXT_COLOR = 0

    def __init__(self):
        self.reset()

    def reset(self):
        self.stations: 'list[Station]' = []
        self.rails: 'list[Rail]' = []

        self.active_rail: Rail = None
        self.active_rail_index: int = None

        self.score: int = 0
        self.available_trains = 5
        self.available_train_upgrades = 3
        self.reset_color()

    def next_color(self):
        color = Data.NEXT_COLOR
        Data.NEXT_COLOR += 1
        return color

    def reset_color(self):
        Data.NEXT_COLOR = 0

    def trains(self):
        for r in self.rails:
            for t in r.trains:
                yield t


data: Data = Data()
