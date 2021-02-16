import pygame as pg
import random
from pygame.constants import K_SPACE
from pygame.event import Event
from util.gui import *
from entities import TrackSegment, Station, Train
from util import *

pg.init()
pg.font.init()
font = pg.font.SysFont('OpenSans-Regular', 24)
SPEED = 60


class MiniMetroGame:
    def __init__(self, w=1000, h=900):
        self.w = w
        self.h = h

        self.dt = 0
        self.passenger_spawn = 0

        # surface = display
        self.display = pg.display.set_mode((self.w, self.h), pg.DOUBLEBUF)
        pg.display.set_caption("MiniMattro")
        self.clock = pg.time.Clock()
        self.layers = [pg.Surface((self.w, self.h), pg.SRCALPHA) for _ in range(5)]

        self.gui = setup_gui([w, h])

        # Build the environment
        self.setup()

    def setup(self):
        data.stations = [Station(Shape.CIRCLE, Vector2(125, 100)),
                         Station(Shape.CIRCLE, Vector2(350, 150)),
                         Station(Shape.CIRCLE, Vector2(300, 350)),
                         Station(Shape.CIRCLE, Vector2(600, 650)),
                         Station(Shape.SQUARE, Vector2(400, 250)),
                         Station(Shape.SQUARE, Vector2(500, 500)),
                         Station(Shape.TRIANGLE, Vector2(100, 450)),
                         Station(Shape.TRIANGLE, Vector2(100, 250))]

        data.create_rail(self.gui)
        data.create_rail(self.gui)
        data.create_rail(self.gui)

    def play_step(self):

        dt = self.dt/1000
        game_over = self.update(dt)
        self.draw()
        self.dt = self.clock.tick(SPEED)

        return game_over

    def update(self, dt):
        # UPDATE GUI
        self.gui.update(dt)
        self.passenger()

        # HANDLE EVENTS
        for event in pg.event.get():
            if self.gui.process_event(event):
                continue
            if event.type == pg.QUIT:
                exit(0)
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                self.left_click_down(event)
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.left_click_up(event)
            elif event.type == pg.MOUSEBUTTONUP and event.button == 3:
                self.right_click_up(event)
            elif event.type == pg.MOUSEMOTION:
                self.mouse_move(event)
            elif event.type == SELECT_TRACK:
                data.set_active_rail(event.track)
            elif event.type == SCORE_POINT:
                data.score += 1
                self.gui.set_score(data.score)
            elif event.type == LOSE_POINT:
                data.score -= 1
                self.gui.set_score(data.score)
            elif event.type == TRAIN_STOP:
                self.train_stop(event)

        # UPDATE TRAINS
        for r in data.rails:
            r.update(dt, data)

        self.passenger_spawn += dt

        # CHECK GAME OVER
        for s in data.stations:
            if s.update():
                return True

        return False

    def draw(self):

        # reset screen
        self.display.fill((100, 100, 100))
        for layer in self.layers:
            layer.fill((0, 0, 0, 0))

        for r in data.rails:
            r.draw(self.layers)

        if data.tmp_segment:
            data.tmp_segment.draw(self.layers[RAIL_LAYER])

        for s in data.stations:
            s.draw(self.layers[STATION_LAYER])

        self.gui.draw(self.layers[GUI_LAYER])

        # show fps
        fps = font.render(str(int(self.clock.get_fps())), False, (255, 255, 255))
        self.display.blit(fps, (self.display.get_size()[0]-fps.get_size()[0], 0))

        # draw each layer
        self.layers[REMOVED_RAIL_LAYER].set_alpha(128)
        for layer in self.layers:
            self.display.blit(layer, (0, 0))

        pg.display.flip()

    def left_click_down(self, event):
        pt = event.pos
        s = self.clip_to_station(pt)
        if s != None and data.active_rail.is_station_valid(s):
            data.tmp_segment = TrackSegment(data.active_rail, data.stations[s].location, (s, None))

    def left_click_up(self, event):
        if data.tmp_segment:
            s = self.clip_to_station(event.pos)
            if s != None and not data.active_rail.is_on_rail(s):
                data.tmp_segment.update_dst(data.stations, data.stations[s].location, s)
                data.active_rail.add_segment(data.tmp_segment, data.stations)
            data.tmp_segment = None

    def right_click_up(self, event):
        s = self.clip_to_station(event.pos)
        if s != None and data.active_rail.can_remove_station(s):
            data.active_rail.remove_station(s)

    def clip_to_station(self, pt):
        for i, s in enumerate(data.stations):
            if s.contains(pt):
                return i
        return None

    def mouse_move(self, event):
        pt = event.pos
        if data.tmp_segment:
            s = self.clip_to_station(pt)
            if data.active_rail.is_on_rail(s):
                s = None
            location = pt if s == None else data.stations[s].location
            data.tmp_segment.update_dst(data.stations, location, s)

        for train in data.trains():
            train.hover = train.is_hovering(pt)

    def train_stop(self, event):
        station: Station = data.stations[event.station]
        train: Train = event.train

        for passenger in station.passengers:
            if not passenger.is_boarding and passenger.should_embark():
                train.embark.append(passenger)
                passenger.is_boarding = True

        for passenger in train.passengers:
            if passenger.should_disembark(station.shape):
                train.disembark.append(passenger)

    def passenger(self):
        dt = self.dt/5000
        self.passenger_spawn += dt

        if self.passenger_spawn > 1:

            randomStation = random.choice(data.stations)
            randomPassenger = random.choice(list(Shape))

            while randomPassenger == randomStation.shape:
                randomStation = random.choice(data.stations)
                randomPassenger = random.choice(list(Shape))

            randomStation.create_passenger(randomPassenger)
            self.passenger_spawn = 0


if __name__ == '__main__':
    game = MiniMetroGame()

    while True:
        game_over = game.play_step()
        if game_over == True:
            break

    print('Final Score', data.score)

    pg.quit()
