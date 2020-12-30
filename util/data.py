from util.constants import *
from entities import Rail, TrackSegment, Station


class Data(object):
    NEXT_COLOR = 0

    def __init__(self):
        self.stations: list[Station] = []
        self.rails: list[Rail] = []

        self.tmp_segment: TrackSegment = None
        self.active_rail: Rail = None

        self.score: int = 0

    def set_active_rail(self, track):
        if track < len(self.rails):
            self.active_rail = self.rails[track]

    def create_rail(self, gui):
        self.rails.append(Rail(COLORS[Data.NEXT_COLOR]))
        Data.NEXT_COLOR += 1

        gui.append_rail(self.rails[-1])


data = Data()
