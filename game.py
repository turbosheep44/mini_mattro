import pygame as pg
from pygame.math import Vector2
from geometry import Pt
from typing import Tuple
from math import ceil

# ########### DATA ###############


class Station(object):
    SQUARE, CIRCLE, TRIANGLE = "square", "circle", "triangle"

    def __init__(self, shape, location: Pt):
        self.shape = shape
        self.location = location
        self.tracks = {}

    def draw(self, screen):
        # SQUARE
        if self.shape == Station.SQUARE:
            pg.draw.rect(screen, (180, 180, 180), pg.Rect(self.location.x-20, self.location.y-20, 40, 40))
            pg.draw.rect(screen, (0, 0, 0), pg.Rect(self.location.x-20, self.location.y-20, 40, 40), 5)

        # CIRCLE
        elif self.shape == Station.CIRCLE:
            pg.draw.circle(screen, (180, 180, 180), self.location.as_tuple(), 25)
            pg.draw.circle(screen, (0, 0, 0), self.location.as_tuple(), 25, 5)

        # TRIANGLE
        elif self.shape == Station.TRIANGLE:
            pg.draw.polygon(screen, (180, 180, 180),
                            [[self.location.x, self.location.y - 25],
                             [self.location.x + 25, self.location.y+17],
                             [self.location.x - 25, self.location.y+17]])
            pg.draw.polygon(screen, (0, 0, 0),
                            [[self.location.x, self.location.y - 25],
                             [self.location.x + 25, self.location.y+17],
                             [self.location.x - 25, self.location.y+17]], 5)

    def contains(self, pt: Pt):
        return (self.location.x-pt.x) ** 2 + (self.location.y-pt.y) ** 2 < 625

    def track_offset(self, direction: Vector2, set: bool):
        dv = (direction.x, direction.y)

        if dv not in self.tracks:
            if set:
                self.tracks[dv] = [True]
            return 0

        if False in self.tracks[dv]:
            index = self.tracks[dv].index(False)
            if set:
                self.tracks[dv][index] = True
        else:
            index = len(self.tracks[dv])
            if set:
                self.tracks[dv].append(True)

        return Station.index_to_offset(index)

    def use_offset(self, direction: Vector2, offset: int):
        # turn the offset back to an index
        index = self.offset_to_index(offset)

        dv = (direction.x, direction.y)

        # make sure the offset list is large enough
        if dv not in self.tracks:
            self.tracks[dv] = [False for _ in range(index+1)]
        else:
            while len(self.tracks[dv]) < index+1:
                self.tracks[dv].append(False)

        self.tracks[dv][index] = True

    def can_use_offset(self, direction, offset):
        dv = (direction.x, direction.y)
        index = self.offset_to_index(offset)
        return not(dv in self.tracks and
                   len(self.tracks[dv]) > index and
                   self.tracks[dv][index])

    @classmethod
    def next_offset(cls, offset: int):
        return Station.index_to_offset(Station.offset_to_index(offset)+1)

    @classmethod
    def offset_to_index(cls, offset: int):
        index = offset * 2
        if index < 0:
            index = abs(index)
        elif index > 0:
            index -= 1
        return index

    @classmethod
    def index_to_offset(cls, index: int):
        return ceil(index / 2) * (-1 if index % 2 == 0 else 1)


class TrackSegment(object):
    CARDINALS = [Vector2(0, 1), Vector2(1, 0), Vector2(0, -1), Vector2(-1, 0),
                 Vector2(1, -1), Vector2(1, 1), Vector2(-1, -1),  Vector2(-1, 1)]
    COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255), (255, 255, 255),
              (125, 0, 125), (125, 125, 0), (0, 125, 125), (0, 0, 0), (125, 0, 0), (0, 125, 0), (0, 0, 125)]
    NEXT_COLOR = 0

    def __init__(self, origin: Pt, dst: Pt, stations: Tuple[int, int]):
        self.origin = origin
        self.dst = dst
        self.stations = stations
        self.color = TrackSegment.COLORS[TrackSegment.NEXT_COLOR]
        TrackSegment.NEXT_COLOR += 1

        self.pts: list[Pt] = [self.origin.as_tuple(),
                              self.origin.as_tuple(),
                              self.dst.as_tuple()]
        self.update_dst(dst, self.stations[1])

    def update_dst(self, dst: Pt, station: int):
        self.dst = dst
        self.stations = (self.stations[0], station)

        # no points required when points are the same
        if self.origin == self.dst:
            self.dst = Pt(self.dst.as_tuple())
            self.dst.y += 1

        # only 1 cardinal required when points lie along a cardinal line
        if self.origin.x == self.dst.x or self.origin.y == self.dst.y or \
                abs(self.origin.x - self.dst.x) == abs(self.origin.y - self.dst.y):

            cardinal = self.origin.vector_to(self.dst)
            cardinal.scale_to_length(cardinal.length()/(abs(cardinal.x) if cardinal.x != 0 else abs(cardinal.y)))
            self.cardinals = [cardinal]
            self.cardinals.append(Vector2(self.cardinals[0]).rotate(180))

            self.recalculate_offsets()
            self.pts = [self.origin.as_tuple(),
                        self.origin_offset().as_tuple(),
                        self.dst_offset().as_tuple(),
                        self.dst.as_tuple()]
            return

        # get the cardinals and work out in which order to use them
        a, b = self.choose_closest_cardinals()
        first, second = Vector2(a), Vector2(b)
        if self.find_order(a, b):
            first, second = second, first
            a, b = b, a

        # set the cardinals and recalculate the offsets
        self.cardinals = [first, second.rotate(180)]
        self.recalculate_offsets()

        # create the points using the cardinals
        p, _ = self.find_factors(a, b, True)
        a.scale_to_length(p * a.length())

        self.pts = [self.origin.as_tuple(),
                    self.origin_offset().as_tuple(),
                    (self.origin_offset() + a).as_tuple(),
                    self.dst_offset().as_tuple(),
                    self.dst.as_tuple()]

    def find_order(self, a: Vector2, b: Vector2) -> bool:
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
            returns `p, q` such that `pa + qb = self.vector()`

            assumes that at exactly one of the values `a.x, a.y, b.x, b.y` is `0`
        """
        v = self.vector(useOffset)

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
        vec = self.vector()
        angles = [abs(cardinal.angle_to(vec)) for cardinal in TrackSegment.CARDINALS]

        smallest = sorted(enumerate(angles), key=lambda a: a[1] if a[1] < 180 else 360 - a[1])

        return Vector2(self.CARDINALS[smallest[0][0]]), Vector2(self.CARDINALS[smallest[1][0]])

    def recalculate_offsets(self, isFinal: bool = False):
        # if the cardinals are opposite (straight line track), then force the offsets to be identical
        # this only actually matters if there is a second station invovled
        if self.stations[1] != None and self.cardinals[0].rotate(180) == self.cardinals[1]:
            # get the first available start offset
            self.start_offset = STATIONS[self.stations[0]].track_offset(self.cardinals[0], False)
            self.end_offset = self.start_offset

            # keep incrementing the offset until the start and end offsets are both accepted by their stations
            while not STATIONS[self.stations[0]].can_use_offset(self.cardinals[0], self.start_offset) \
                    or not STATIONS[self.stations[1]].can_use_offset(self.cardinals[1], self.end_offset):

                self.start_offset = Station.next_offset(self.start_offset)
                self.end_offset = self.start_offset

            if isFinal:
                for i, offset in zip(range(2), (self.start_offset, self.end_offset)):
                    STATIONS[self.stations[i]].use_offset(self.cardinals[i], offset)

            return

        # cardinals are not opposite, use normal method
        self.start_offset = STATIONS[self.stations[0]].track_offset(self.cardinals[0], isFinal)
        if self.stations[1] != None:
            self.end_offset = STATIONS[self.stations[1]].track_offset(self.cardinals[1], isFinal)
        else:
            self.end_offset = 0

    def origin_offset(self):
        return self.__offset_pt__(self.origin, self.cardinals[0], self.start_offset)

    def dst_offset(self):
        return self.__offset_pt__(self.dst, self.cardinals[1], self.end_offset)

    def __offset_pt__(self, pt: Pt, relative_to: Vector2, amount: int):
        offset = pt.clone()
        if relative_to.y == 0:
            offset.y += amount*-10
        else:
            offset.x += amount*10

        return offset

    def realise(self):
        self.recalculate_offsets(True)

    def vector(self, useOffset: bool = False):
        return self.origin.vector_to(self.dst) if not useOffset else\
            self.origin_offset().vector_to(self.dst_offset())

    def draw(self):
        if not len(self.pts):
            return

        pg.draw.lines(screen, self.color, False, self.pts, 10)
        for joint in self.pts:
            pg.draw.circle(screen, self.color, joint, 5)


class Railway(object):

    RED, GREEN, BLUE = (100, 0, 0), (0, 100, 0), (0, 0, 100)

    def __init__(self,  color):
        self.color = color
        self.stations: list[int] = []
        self.track_segments: list[TrackSegment] = []
        self.trains: list[Train] = []

    def addStation(self, id, index):
        self.stations.insert(index, id)

    def draw(self, screen, stations):
        if not self.stations:
            return

    def update(self, dt):
        for t in self.trains:
            t.update(dt, 100)


class Train(object):
    SPEED = 50

    def __init__(self):
        self.position = 0
        self.direction = -1

    def update(self, dt, end):
        self.position += self.direction * Train.SPEED

        # bounce off end
        if self.position > end:
            self.position -= 2*(self.position - end)
            self.direction *= -1

        # bounce off start
        elif self.position < 0:
            self.position *= -1
            self.direction *= -1


STATIONS = [Station(Station.CIRCLE, Pt((125, 100))),
            Station(Station.CIRCLE, Pt((350, 150))),
            Station(Station.CIRCLE, Pt((300, 350))),
            Station(Station.CIRCLE, Pt((600, 650))),
            Station(Station.SQUARE, Pt((400, 250))),
            Station(Station.SQUARE, Pt((500, 500))),
            Station(Station.TRIANGLE, Pt((100, 450))),
            Station(Station.TRIANGLE, Pt((100, 250)))]

TRACKS = []

# RAILS = [Railway(Railway.RED),
#          Railway(Railway.GREEN),
#          Railway(Railway.BLUE), ]

# RAILS[0].stations = [1, 3, 5]
# RAILS[1].stations = [0, 2, 4]

# ############## GAME ################

tmp_track: TrackSegment = None


def update(dt):
    global tmp_track

    for event in pg.event.get():
        if event.type == pg.QUIT:
            exit(0)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            s = clip_to_station(event.pos)
            if s != -1:
                tmp_track = TrackSegment(STATIONS[s].location, Pt(event.pos), (s, None))

        elif event.type == pg.MOUSEBUTTONDOWN:
            print()
            for s in STATIONS:
                print(s.tracks)

        elif event.type == pg.MOUSEBUTTONUP:
            if tmp_track:
                s = clip_to_station(event.pos)
                if s != -1:
                    tmp_track.update_dst(STATIONS[s].location, s)
                    tmp_track.realise()
                    TRACKS.append(tmp_track)
                tmp_track = None

        elif event.type == pg.MOUSEMOTION:
            if tmp_track:
                s = clip_to_station(event.pos)
                station = None if s == -1 else s
                location = Pt(event.pos) if s == -1 else STATIONS[s].location

                tmp_track.update_dst(location, station)


def clip_to_station(pt):
    for i, s in enumerate(STATIONS):
        if s.contains(Pt(pt)):
            return i

    return -1


def draw():
    screen.fill((100, 100, 100))

    if tmp_track:
        tmp_track.draw()

    for t in TRACKS:
        t.draw()

    for s in STATIONS:
        s.draw(screen)

    # show fps
    fps = font.render(str(int(clock.get_fps())), False, (255, 255, 255))
    screen.blit(fps, (screen.get_size()[0]-fps.get_size()[0], 0))

    pg.display.flip()


# ############ BOOTSTRAP ############
pg.init()
pg.font.init()

screen = pg.display.set_mode([1000, 900])
pg.display.set_caption("MiniMattro")

clock = pg.time.Clock()
font = pg.font.SysFont('OpenSans-Regular', 24)
dt = 0

running = False
while not running:
    dt = clock.tick(60)
    # update
    update(dt)

    # display
    draw()
