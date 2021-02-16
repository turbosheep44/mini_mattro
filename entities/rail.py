from entities.station import Station
from entities.segment import TrackSegment
from entities.train import Train
from typing import List
import pygame as pg
from util.constants import RAIL_LAYER, REMOVED_RAIL_LAYER, TRAIN_LAYER


class Rail(object):
    def __init__(self, color):
        self.color = color
        self.segments: 'list[TrackSegment]' = []
        self.destroyed_segments: 'list[TrackSegment]' = []
        self.trains: 'list[Train]' = []

    def __str__(self):
        if len(self.segments) != 0:
            return f'[ {", ".join([f"{segment.stations[0]}:{segment.stations[1]}" for segment in self.segments])} ]'
        return "[]"

    def update(self, dt, data):
        for train in self.trains:
            train.update(dt, data)

        for segment in self.destroyed_segments:
            # finally remove the segment permanently when
            # there are no trains which require this segment to rejoin the non-destroyed track
            if not segment.required_by_train():
                self.destroyed_segments.remove(segment)
                segment.free_offsets(data.stations)

    def draw(self, layers):
        for segment in self.segments:
            segment.draw(layers[RAIL_LAYER])

        for segment in self.destroyed_segments:
            segment.draw(layers[REMOVED_RAIL_LAYER])

        for train in self.trains:
            train.draw(layers[TRAIN_LAYER])

    def remove_station(self, s):
        """
        removes the station from the rail by deleting the associated segment

        can_delete_station(s) should return true or else behaviour of this method is undefined
        """

        # find the segment and remove it from the main list
        to_remove = self.segments[0] if s == self.start_station() else self.segments[-1]
        self.segments.remove(to_remove)

        # mark for full deletion later (in update)
        to_remove.should_delete = True
        self.destroyed_segments.append(to_remove)

        # remove connections of other segments
        if to_remove.previous:
            to_remove.previous.next = None
        if to_remove.next:
            to_remove.next.previous = None

        # if there are no more segments, mark the trains for end of life
        if len(self.segments) == 0:
            for train in self.trains:
                train.end_of_life = True

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

    def is_station_valid(self, i) -> bool:
        """
        checks if a station is valid to start a new track segment
        a valid station is either at the start or the end of the line
        """
        # line is shutting down, cant build a new segment
        if len(self.segments) == 0 and len(self.destroyed_segments) != 0:
            return False

        # line is empty, all stations valid
        if len(self.segments) == 0:
            return True

        # only start and end stations are valid
        return i == self.segments[0].stations[0] or i == self.segments[-1].stations[1]

    def is_on_rail(self, i) -> bool:
        """
        determines whether the station is on this line
        """
        if len(self.segments) == 0:
            return False

        for segment in self.segments:
            if segment.stations[0] == i:
                return True

        return self.segments[-1].stations[1] == i

    def can_remove_station(self, s) -> bool:
        """
            checks whether the station can be removed from this rail

            will return true if the station is at the start or at the end of this rail
        """
        if len(self.segments) == 0:
            return False
        return s == self.start_station() or s == self.end_station()

    def start_station(self):
        return self.segments[0].stations[0]

    def end_station(self):
        return self.segments[-1].stations[1]
