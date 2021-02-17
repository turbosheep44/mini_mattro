from entities.station import Station
from entities.segment import TrackSegment
from entities.train import Train
from typing import List
import pygame as pg
from util.constants import REQUEST_TRAIN, RAIL_LAYER, REMOVED_RAIL_LAYER, TRAIN_LAYER


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

    def remove_station(self, s, stations: 'list[Station]'):
        """
        removes the station `s` from the rail by deleting the associated segment,
        requires a list of all `stations`

        can_delete_station(s) should return true or else behaviour of this method is undefined
        """

        # find the segment(s) and remove them from the segment list
        to_remove = [segment for segment in self.segments if s in segment.stations]
        first_removed_index = self.segments.index(to_remove[0])
        for remove in to_remove:
            self.segments.remove(remove)

            # mark for full deletion later (in update)
            self.destroyed_segments.append(remove)

        # if this was not an end station, make a new segment to bridge the gap
        new_segment = None
        if len(to_remove) == 2:
            start = to_remove[0].stations[0]
            end = to_remove[-1].stations[-1]
            new_segment = TrackSegment(self, stations[start].location, (start, None))
            new_segment.update_dst(stations, end)

            # insert the new segment and realise it
            self.segments.insert(first_removed_index, new_segment)
            new_segment.realise(stations)

            # connect the new segment to adjacent rails
            new_segment.previous = to_remove[0].previous
            new_segment.next = to_remove[-1].next

            # solve the edge case when there the station removed is the penultimate in the line
            if not to_remove[0].previous:
                to_remove[0].end_of_line_jump = new_segment
            if not to_remove[1].next:
                to_remove[1].end_of_line_jump = new_segment

        # replace connections of other segments with a connection to new segment (or None)
        if to_remove[0].previous:
            to_remove[0].previous.next = new_segment
        if to_remove[-1].next:
            to_remove[-1].next.previous = new_segment

        # if there are no more segments, mark the trains for end of life
        if len(self.segments) == 0:
            for train in self.trains:
                train.end_of_life = True

    def add_segment(self, segment: TrackSegment, stations: List[Station]):
        """
        adds a segment to the start or the end of the rail

            - if this is the first segment in the rail then a train is also created
            - if the segment is not in the correct order it is flipped
        """
        # first segment, add to list and automatically fire an add train event
        if len(self.segments) == 0:
            self.segments.append(segment)
            self.trains = []
            self.segments[0].realise(stations)
            pg.event.post(pg.event.Event(REQUEST_TRAIN))

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
        """
        return self.is_on_rail(s)

    def start_station(self):
        return self.segments[0].stations[0]

    def end_station(self):
        return self.segments[-1].stations[1]
