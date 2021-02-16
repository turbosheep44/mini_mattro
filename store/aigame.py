import pygame as pg
import random
import numpy as np

from pygame.constants import K_SPACE
from gui import setup_gui
from entities import TrackSegment, Station, Train
from util import *


def setup():
    data.stations = [Station(Shape.CIRCLE, Vector2(125, 100)),
                     Station(Shape.SQUARE, Vector2(500, 500)),
                     Station(Shape.TRIANGLE, Vector2(100, 250))]

    data.create_rail(gui)
    data.create_rail(gui)
    data.create_rail(gui)


temp_count = 0


sample_action = np.array([1, 0, 0, 0, 1, 1, 1, 0, 0])
sample_action_two = np.array([1, 0, 0, 1, 1, 0, 1, 0, 0])


def passenger(dt):

    global passenger_spawn
    passenger_spawn += dt

    if passenger_spawn > 1:

        # TEMPORARY STUFF

        global temp_count
        temp_count = temp_count + 1

        if temp_count == 3:
            create_action(sample_action)

        if temp_count == 5:
            create_action(sample_action_two)

        randomStation = random.choice(data.stations)
        randomPassenger = random.choice(list(Shape))

        while randomPassenger == randomStation.shape:
            randomStation = random.choice(data.stations)
            randomPassenger = random.choice(list(Shape))

        randomStation.create_passenger(randomPassenger)
        passenger_spawn = 0


def create_rail(s1, s2, r):
    print(s1 + s2 + r)

    rail = data.rails[r]
    station_one = data.stations[s1]
    station_two = data.stations[s2]

    if len(rail.segments) == 0:

        tmp_segment = TrackSegment(rail, station_one.location, (s1, None))
        tmp_segment.update_dst(data.stations, station_two.location, s2)
        rail.add_segment(tmp_segment, data.stations)

        print(rail)

    else:

        if rail.is_on_rail(s1) and rail.is_on_rail(s2):
            print("invalid")
            return

        if not rail.is_on_rail(s1) and not rail.is_on_rail(s2):
            print("invalid")
            return

        start = data.stations[rail.start_station()]
        end = data.stations[rail.end_station()]

        if station_one in [start, end]:

            temp_segment = TrackSegment(rail, station_one.location, (s1, None))
            temp_segment.update_dst(data.stations, station_two.location, s2)

            rail.add_segment(temp_segment, data.stations)

        if station_two in [start, end]:

            temp_segment = TrackSegment(rail, station_two.location, (s2, None))
            temp_segment.update_dst(data.stations, station_one.location, s1)

            rail.add_segment(temp_segment, data.stations)


def create_action(action):

    r = np.where(action[0:3] == 1)[0][0]

    s1 = np.where(action[3:-3] == 1)[0][0]
    s2 = np.where(action[3:-3] == 1)[0][1]

    # TODO: Add Connect/Disconnect/ Do Nothing detection

    create_rail(s1, s2, r)


def update(dt, action=None):
    gui.update(dt)

    for event in pg.event.get():

        if gui.process_event(event):
            continue

        if event.type == pg.QUIT:
            exit(0)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            left_click_down(event)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            left_click_up(event)
        elif event.type == pg.MOUSEMOTION:
            mouse_move(event)
        elif event.type == SELECT_TRACK:
            data.set_active_rail(event.track)
        elif event.type == SCORE_POINT:
            data.score += 1
            gui.set_score(data.score)
        elif event.type == LOSE_POINT:
            print("losing point")
            data.score -= 1
            gui.set_score(data.score)
        elif event.type == TRAIN_STOP:
            train_stop(event)
        elif event.type == pg.KEYDOWN:
            remove_segment(event)    # TODO: Set reward to minus 10 when 6 passengers are on the same
    # station

    for r in data.rails:
        r.update(dt, data)

    global passenger_spawn
    passenger_spawn += dt


def remove_segment(event):
    if(event.key == pg.K_UP):
        data.active_rail.remove_segment(data.active_rail.segments[-1])
    elif(event.key == pg.K_DOWN):
        data.active_rail.remove_segment(data.active_rail.segments[0])


def train_stop(event):
    station: Station = data.stations[event.station]
    train: Train = event.train

    if(len(train.passengers) < 7):
        for passenger in station.passengers:
            print("Picking Up Someone")
            if passenger.should_embark():
                train.embark.append(passenger)

    for passenger in train.passengers:
        if passenger.should_disembark(station.shape):
            train.disembark.append(passenger)


def left_click_down(event):
    pt = event.pos
    s = clip_to_station(pt)
    if s != None and data.active_rail.is_station_valid(s):
        data.tmp_segment = TrackSegment(data.active_rail, data.stations[s].location, (s, None))


def left_click_up(event):
    if data.tmp_segment:
        # add the segment to the rail if mouse is released on a station which is not already part of the rail
        s = clip_to_station(event.pos)
        if s != None and not data.active_rail.is_on_rail(s):
            data.tmp_segment.update_dst(data.stations, data.stations[s].location, s)
            data.active_rail.add_segment(data.tmp_segment, data.stations)
        data.tmp_segment = None


def mouse_move(event):

    pt = event.pos

    if data.tmp_segment:
        s = clip_to_station(pt)
        if data.active_rail.is_on_rail(s):
            s = None

        location = pt if s == None else data.stations[s].location

        data.tmp_segment.update_dst(data.stations, location, s)


def clip_to_station(pt):

    # clip to station first
    for i, s in enumerate(data.stations):
        if s.contains(pt):
            return i

    return None


def draw():
    # clear the screen
    surface.fill((100, 100, 100))
    for layer in layers:
        layer.fill((0, 0, 0, 0))

    for r in data.rails:
        r.draw(layers)

    if data.tmp_segment:
        data.tmp_segment.draw(layers[0])

    for s in data.stations:
        s.draw(layers[-1])

    gui.draw(layers[-1])

    # show fps
    fps = font.render(str(int(clock.get_fps())), False, (255, 255, 255))
    surface.blit(fps, (surface.get_size()[0]-fps.get_size()[0], 0))

    # draw each layer
    for layer in layers:
        surface.blit(layer, (0, 0))
    pg.display.flip()


def reset():

    data.score = 0
    gui.set_score(data.score)

    for station in data.stations:
        station.passengers = []

    for rail in data.rails:
        rail.segments = []
        rail.trains = []

    # dt = clock.tick(60)
pg.init()
pg.font.init()
pg.display.set_caption("MiniMattro")

surface = pg.display.set_mode([1000, 900], pg.DOUBLEBUF)
layers = [pg.Surface([1000, 900], pg.SRCALPHA) for _ in range(3)]

clock = pg.time.Clock()
font = pg.font.SysFont('OpenSans-Regular', 24)
dt = 0

gui = setup_gui([1000, 900])
setup()

passenger_spawn = 0

running = False

while not running:

    dt = clock.tick(60)
    update(dt/1000)
    passenger(dt/5000)

    draw()
