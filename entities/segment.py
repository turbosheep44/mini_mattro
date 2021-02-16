from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from entities.rail import Rail

from util.draw import ortholine
from pygame.math import Vector2
from typing import Tuple
from util.constants import *
from entities.station import Station
from typing import List


class TrackSegment(object):
    def __init__(self, rail, origin, stations: Tuple[int, int]):
        self.origin: Vector2 = Vector2(origin)
        self.dst: Vector2 = Vector2(0, 0)
        self.stations = stations
        self.rail: Rail = rail

        self.end_of_line_jump: TrackSegment = None
        self.is_realised: bool = False
        self.length: float = -1
        self.lengths: 'list[float]' = []
        self.vectors: 'list[Vector2]' = []
        self.position_update: float = 0
        self.previous: TrackSegment = None
        self.next: TrackSegment = None

        self.pts: 'list[Vector2]' = []

    def update_dst(self, stations: List[Station], station: int, pt: 'Tuple[int, int]' = None):
        """
        update_dst sets a new station to be the new destination of this track segment,
        recalculating offsets and drawing points

        if `station` is `None`, then `pt` should be provided as the location of the end of the segment
        """
        if self.is_realised:
            raise ValueError("cannot call update_dst on a track segment which has been realised")

        self.dst = Vector2(stations[station].location if not station == None else pt)
        self.stations = (self.stations[0], station)

        # no points required when points are the same
        if self.origin == self.dst:
            self.dst.y += 1

        # only 1 cardinal required when points lie along a cardinal line
        if self.origin.x == self.dst.x or self.origin.y == self.dst.y or \
                abs(self.origin.x - self.dst.x) == abs(self.origin.y - self.dst.y):

            cardinal = self.dst - self.origin
            cardinal.scale_to_length(cardinal.length() / (abs(cardinal.x) if cardinal.x != 0 else abs(cardinal.y)))
            self.cardinals = [cardinal]
            self.cardinals.append(self.cardinals[0].rotate(180))

            self.recalculate_offsets(stations)
            self.pts = [self.origin, self.origin_offset(),
                        self.dst_offset(), self.dst]
            return

        # get the cardinals and work out in which order to use them
        a, b = self.choose_closest_cardinals()
        first, second = Vector2(a), Vector2(b)
        if self.find_order(a, b):
            first, second = second, first
            a, b = b, a

        # set the cardinals and recalculate the offsets
        self.cardinals = [first, second.rotate(180)]
        self.recalculate_offsets(stations)

        # create the points using the cardinals
        p, _ = self.find_factors(a, b, True)
        a.scale_to_length(p * a.length())

        self.pts = [self.origin, self.origin_offset(),
                    (self.origin_offset() + a),
                    self.dst_offset(), self.dst]

    def find_order(self, a: Vector2, b: Vector2) -> bool:
        """
        find_order decides whether `a` or `b` should be used first when constructing the track
        the vector is chosen to create the smallest movement in the line possible (assuming it exists)

        the boolean returned indicates whether the vectors should be swapped
        """

        # line does not yet exist (order does not matter)
        if len(self.pts) == 0:
            return False

        p, q = self.find_factors(a, b)
        a.scale_to_length(p * a.length())
        b.scale_to_length(q * b.length())

        # if using `a` first results in less movement to the current vector
        # then dont swap
        if (self.origin + a).distance_to(self.pts[2]) < \
                (self.origin + b).distance_to(self.pts[2]):
            return False
        return True

    def find_factors(self, a: Vector2, b: Vector2, useOffset: bool = False):
        """
            returns `p, q` such that `pa + qb = self.dst - self.origin`

            assumes that at exactly one of the values `a.x, a.y, b.x, b.y` is `0`
            because one of the cardinals will always be either horizontal or vertical
        """
        v = self.dst - self.origin if not useOffset else self.dst_offset() - self.origin_offset()

        # p*a_x + q*b_x = v_x
        # p*a_y + q*b_y = v_y

        zero, other, reversed = \
            (a, b, False) \
            if a.x == 0 or a.y == 0 \
            else (b, a, True)

        if zero.x == 0:
            q = v.x / other.x
            p = (v.y - (q * other.y)) / zero.y
        else:
            q = v.y / other.y
            p = (v.x - (q * other.x)) / zero.x

        return (p, q) if not reversed else (q, p)

    def choose_closest_cardinals(self) -> Tuple[Vector2, Vector2]:
        dv = self.dst - self.origin
        angles = [abs(cardinal.angle_to(dv)) for cardinal in CARDINALS]

        smallest = sorted(enumerate(angles), key=lambda a: a[1] if a[1] < 180 else 360 - a[1])

        return Vector2(CARDINALS[smallest[0][0]]), Vector2(CARDINALS[smallest[1][0]])

    def recalculate_offsets(self, stations: 'list[Station]', isFinal: bool = False):
        # if the cardinals are opposite (straight line track), then force the offsets to be identical
        # this only actually matters if there is a second station involved
        if self.stations[1] != None and self.cardinals[0].rotate(180) == self.cardinals[1]:
            # get the first available start offset
            self.start_offset = stations[self.stations[0]].track_offset(self.cardinals[0], False)
            self.end_offset = self.start_offset

            # keep incrementing the offset until the start and end offsets are both accepted by their stations
            while not stations[self.stations[0]].can_use_offset(self.cardinals[0], self.start_offset) \
                    or not stations[self.stations[1]].can_use_offset(self.cardinals[1], self.end_offset):

                self.start_offset = Station.next_offset(self.start_offset)
                self.end_offset = self.start_offset

            if isFinal:
                stations[self.stations[0]].use_offset(self.cardinals[0], self.start_offset)
                stations[self.stations[1]].use_offset(self.cardinals[1], self.end_offset)

            return

        # cardinals are not opposite, use normal method
        self.start_offset = stations[self.stations[0]].track_offset(self.cardinals[0], isFinal)
        if self.stations[1] != None:
            self.end_offset = stations[self.stations[1]].track_offset(self.cardinals[1], isFinal)
        else:
            self.end_offset = 0

    def origin_offset(self) -> Tuple[int, int]:
        return self.__offset_pt__(self.origin, self.cardinals[0], self.start_offset)

    def dst_offset(self) -> Tuple[int, int]:
        return self.__offset_pt__(self.dst, self.cardinals[1], self.end_offset)

    def __offset_pt__(self, pt, relative_to: Vector2, amount: int) -> Vector2:
        if relative_to.y == 0:
            return pt + (0, (amount*-10))
        else:
            return pt + ((amount*-10), 0)

    def free_offsets(self, stations: 'list[Station]'):
        """
        used to tell the stations which this segment connects to that the offsets it used are no longer in use
        """
        stations[self.stations[0]].free_offset(self.cardinals[0], self.start_offset)
        stations[self.stations[1]].free_offset(self.cardinals[1], self.end_offset)

    def realise(self, stations: List[Station]):
        """
        realise recalculates and locks in the co-ordinates of the track segment

        after realisation, calls to update_dst are invalid and will raise an exception
        """
        self.recalculate_offsets(stations, True)
        self.is_realised = True

        self.lengths = [src.distance_to(dst) for (src, dst) in zip(self.pts, self.pts[1:])]
        self.length = sum(self.lengths)
        self.vectors = [dst-src for (src, dst) in zip(self.pts, self.pts[1:])]
        self.position_update = TRAIN_SPEED / self.length

    def draw(self, surface):
        if not len(self.pts):
            return

        for start, end in zip(self.pts, self.pts[1:]):
            ortholine(surface, self.rail.color, start, end, 10, rounded=True)

    def lerp_position(self, position) -> Tuple[Vector2, Vector2]:
        """
        provided with a position in the range [0, 1] this function returns a 
        set of co-ordinates and a direction vector for a train which is that percentage 
        along the track

        track must be realised to call this function
        """
        if not self.is_realised:
            raise ValueError("cannot lerp position before track segement is realised")

        if position < 0 or position > 1:
            raise ValueError("cannot lerp to a position outside of the range [0, 1]")

        position = self.length * position
        if position == 0:
            position = 0.001
        elif position == 1:
            position = 0.999

        i = 0
        try:
            while position > self.lengths[i]:
                position -= self.lengths[i]
                i += 1
        except IndexError:
            #! AI causes this index error, not sure why
            print("Index Error")
            i -= 1

        # train is between points i and i+1, (position*100 / self.lengths[i])% of the way
        dv = self.vectors[i]

        try:
            dv.scale_to_length(position)
        except ValueError:
            #! AI causes this value error, not sure why
            print("Value Error")

        pt = self.pts[i] + dv
        return pt, Vector2(dv)

    def next_segment(self, direction) -> 'Tuple[TrackSegment, int]':
        """
        returns the next segment that a train must visit on this segment and the new direction of travel
        """
        # continue forwards
        if direction == 1 and self.next != None:
            return self.next, direction

        # continue backwards
        elif direction == -1 and self.previous != None:
            return self.previous, direction

        # end of line, turn around
        return (self.end_of_line_jump or self), direction * -1

    def required_by_train(self):
        for train in self.rail.trains:
            segment, direction = train.current_segment, train.direction
            while segment not in self.rail.segments:
                if segment == self:
                    return True
                segment, direction = segment.next_segment(direction)

        return False

    def reverse(self):
        self.stations = self.stations[::-1]
        self.origin, self.dst = self.dst, self.origin
        self.cardinals.reverse()
        self.pts.reverse()
