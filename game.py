import pygame as pg
from pygame.constants import K_SPACE

from gui import setup_gui
from entities import TrackSegment, Station
from util import *

# ########### TMP ###############


def setup():
    data.stations = [Station(Station.CIRCLE, Vector2(125, 100)),
                     Station(Station.CIRCLE, Vector2(350, 150)),
                     Station(Station.CIRCLE, Vector2(300, 350)),
                     Station(Station.CIRCLE, Vector2(600, 650)),
                     Station(Station.SQUARE, Vector2(400, 250)),
                     Station(Station.SQUARE, Vector2(500, 500)),
                     Station(Station.TRIANGLE, Vector2(100, 450)),
                     Station(Station.TRIANGLE, Vector2(100, 250))]

    data.create_rail(gui)
    data.create_rail(gui)
    data.create_rail(gui)

# ############## GAME ################


def update(dt):
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
        elif event.type == pg.KEYDOWN and event.key == K_SPACE:
            pg.event.post(pg.event.Event(SCORE_POINT))

    for r in data.rails:
        r.update(dt)


def left_click_down(event):
    s = clip_to_station(event.pos)
    if s != None and data.active_rail.is_station_valid(s):
        data.tmp_segment = TrackSegment(data.active_rail.color, data.stations[s].location, (s, None))


def left_click_up(event):
    if data.tmp_segment:
        # add the segment to the rail if mouse is released on a station which is not already part of the rail
        s = clip_to_station(event.pos)
        if s != None and not data.active_rail.is_on_rail(s):
            data.tmp_segment.update_dst(data.stations, data.stations[s].location, s)
            data.active_rail.add_segment(data.tmp_segment, data.stations)
        data.tmp_segment = None


def mouse_move(event):
    if data.tmp_segment:
        s = clip_to_station(event.pos)
        if data.active_rail.is_on_rail(s):
            s = None

        location = event.pos if s == None else data.stations[s].location

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


# ############ BOOTSTRAP ############
pg.init()
pg.font.init()

surface = pg.display.set_mode([1000, 900], pg.DOUBLEBUF)
layers = [pg.Surface([1000, 900], pg.SRCALPHA) for _ in range(3)]

pg.display.set_caption("MiniMattro")

clock = pg.time.Clock()
font = pg.font.SysFont('OpenSans-Regular', 24)
dt = 0

gui = setup_gui([1000, 900])

setup()

running = False
while not running:
    dt = clock.tick(60)
    # update
    update(dt/1000)

    # display
    draw()
