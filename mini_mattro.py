
import random
from pygame.constants import K_SPACE
from pygame.event import Event
from util.gui import *
from entities import TrackSegment, Station, Train
from util import *
from abc import ABC, abstractmethod
import pygame as pg

pg.init()
pg.font.init()
font = pg.font.SysFont('OpenSans-Regular', 24)
FPS = 60


class MiniMattro(ABC):

    def __init__(self, w=1000, h=900):
        self.w = w
        self.h = h

        self.passenger_spawn = 0
        self.gui: GUI = None
        self.reset()

        # surface = display
        pg.display.set_caption("MiniMattro")
        self.display = pg.display.set_mode((self.w, self.h), pg.DOUBLEBUF)
        self.clock = pg.time.Clock()
        self.layers = [pg.Surface((self.w, self.h), pg.SRCALPHA) for _ in range(5)]

    def reset(self):
        reset_data()
        data.stations = [Station(Shape.CIRCLE, Vector2(125, 100)),
                         Station(Shape.CIRCLE, Vector2(350, 150)),
                         Station(Shape.CIRCLE, Vector2(300, 350)),
                         Station(Shape.CIRCLE, Vector2(600, 650)),
                         Station(Shape.SQUARE, Vector2(400, 250)),
                         Station(Shape.SQUARE, Vector2(500, 500)),
                         Station(Shape.TRIANGLE, Vector2(100, 450)),
                         Station(Shape.TRIANGLE, Vector2(100, 250))]
        self.gui = setup_gui([self.w, self.h])
        self.create_rail()
        self.create_rail()
        self.create_rail()

    @abstractmethod
    def play_step(self):
        pass

    @abstractmethod
    def handle_events(self, event: Event) -> None:
        pass

    def update(self, dt) -> bool:
        # UPDATE GUI
        self.passenger(dt)

        # HANDLE EVENTS
        events = []
        for event in pg.event.get():
            if self.gui.process_event(event):
                continue

            events.append(event)

            if event.type == pg.QUIT:
                exit(0)
            elif event.type == SELECT_TRACK:
                data.active_rail = data.rails[event.track]
                data.active_rail_index = event.track
            elif event.type == SCORE_POINT:
                data.score += 1
                self.gui.update_values()
            elif event.type == TRAIN_STOP:
                self.train_stop(event)
            elif event.type == REQUEST_TRAIN:
                self.add_train(data.rails.index(event.rail))
            elif event.type == UPGRADE_TRAIN:
                self.upgrade_train(event.train)
            elif event.type == EOL_TRAIN:
                self.delete_train(event.train)

        self.handle_events(events)

        # UPDATE TRAINS
        for r in data.rails:
            r.update(dt, data)

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

        if hasattr(self, "tmp_segment") and self.tmp_segment:
            self.tmp_segment.draw(self.layers[RAIL_LAYER])

        for s in data.stations:
            s.draw(self.layers[STATION_LAYER])

        self.gui.draw(self.layers[GUI_LAYER])

        # show fps
        fps = font.render(f"FPS: {int(self.clock.get_fps())}", False, (255, 255, 255))
        self.display.blit(fps, (10, self.display.get_size()[1]-fps.get_size()[1]-10))

        # draw each layer
        self.layers[REMOVED_RAIL_LAYER].set_alpha(128)
        for layer in self.layers:
            self.display.blit(layer, (0, 0))

        pg.display.flip()

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

    def passenger(self, dt):
        self.passenger_spawn += dt

        if self.passenger_spawn > 2:

            randomStation = random.choice(data.stations)
            randomPassenger = random.choice(list(Shape))

            while randomPassenger == randomStation.shape:
                randomStation = random.choice(data.stations)
                randomPassenger = random.choice(list(Shape))

            randomStation.create_passenger(randomPassenger)
            self.passenger_spawn = 0

    def create_rail(self):
        data.rails.append(Rail(COLORS[data.next_color()]))
        self.gui.append_rail(data.rails[-1])

    def add_train(self, r: int):
        rail: Rail = data.rails[r]
        if data.available_trains < 1 or len(rail.segments) < 1:
            return

        data.available_trains -= 1
        rail.trains.append(Train(random.choice(rail.segments)))
        pg.event.post(pg.event.Event(TRAINS_CHANGED))

    def upgrade_train(self, train: Train):
        if not train or data.available_train_upgrades < 1 or train.is_upgraded:
            return

        data.available_train_upgrades -= 1
        train.is_upgraded = True
        pg.event.post(pg.event.Event(TRAINS_CHANGED))

    def delete_train(self, train: Train):
        train.current_segment.rail.trains.remove(train)
        data.available_trains += 1
        if train.is_upgraded:
            data.available_train_upgrades += 1
        pg.event.post(pg.event.Event(TRAINS_CHANGED))

    def connect(self, s1: int, s2: int, r: int):
        rail = data.rails[r]
        if not rail.is_station_valid(s1) or rail.is_on_rail(s2):
            print("invalid connect action")
            return

        segment = TrackSegment(rail, data.stations[s1].location, (s1, None))
        segment.update_dst(data.stations, s2)
        rail.add_segment(segment, data.stations)

    def remove_station(self, s: int, r: int):
        if not data.rails[r].can_remove_station(s):
            print("invalid remove action")
            return

        data.rails[r].remove_station(s, data.stations)
