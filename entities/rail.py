from entities.station import Station
from entities.segment import TrackSegment
from entities.train import Train
from typing import List


class Rail(object):
    def __init__(self, color):
        self.color = color
        self.segments: list[TrackSegment] = []
        self.trains: list[Train] = []

    def __str__(self):
        if len(self.segments) != 0:
            return f'[ {", ".join([f"{segment.stations[0]}:{segment.stations[1]}" for segment in self.segments])} ]'
        return "[]"

    def update(self, dt, data):
        for train in self.trains:
            train.update(dt, data)

    def draw(self, layers):
        for segment in self.segments:
            segment.draw(layers[0])

        for train in self.trains:
            train.draw(layers[1])

    def add_segment(self, segment: TrackSegment, stations: List[Station]):
        # first segment, add to list and automatically create a train
        if len(self.segments) == 0:
            self.segments.append(segment)
            self.trains = [Train(segment)]
            self.segments[0].realise(stations)
        # if the segment originates at the start of the line, then prepend it to the segment list (and flip it)
        # otherwise append it to the segment list
        elif self.segments[0].stations[0] == segment.stations[0]:
            segment.reverse()
            self.segments.insert(0, segment)
            self.segments[0].realise(stations)
        else:
            self.segments.append(segment)
            self.segments[-1].realise(stations)

        # update the previous and next pointers
        if len(self.segments) == 1:
            self.segments[0].previous, self.segments[0].next = None, None
        else:
            # there are at least 2 segments
            first, last = self.segments[0], self.segments[-1]
            first.previous, first.next = None, self.segments[1]
            last.previous, last.next = self.segments[-2], None
            for i in range(1, len(self.segments)-1):
                self.segments[i].previous, self.segments[i].next = self.segments[i-1], self.segments[i+1]

    def is_station_valid(self, i):
        """
        checks if a station is valid to start a new track segment
        a valid station is either at the start or the end of the line
        """
        # line is empty, all stations valid
        if len(self.segments) == 0:
            return True

        # only start and end stations are valid
        return i == self.segments[0].stations[0] or i == self.segments[-1].stations[1]

    def is_on_rail(self, i):
        """
        determines whether the station is on this line
        """
        if len(self.segments) == 0:
            return False

        for segment in self.segments:
            if segment.stations[0] == i:
                return True

        return self.segments[-1].stations[1] == i
