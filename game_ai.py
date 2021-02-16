import pygame as pg
import random
from pygame.constants import K_SPACE
from util.gui import *
from entities import TrackSegment, Station, Train
from util import *
from util.gui import setup_gui
import numpy as np
import enum

pg.init()
pg.font.init()
font = pg.font.SysFont('OpenSans-Regular', 24)
SPEED = 60


class Mode(enum.Enum):
    DoNothing = 0
    Connect = 1
    Disconnect = 2


class MiniMetroGameAI:
    def __init__(self, w=1000, h=900):
        self.w = w
        self.h = h

        self.display = pg.display.set_mode((self.w, self.h), pg.DOUBLEBUF)
        pg.display.set_caption("MiniMattro")
        self.clock = pg.time.Clock()
        self.layers = [pg.Surface((self.w, self.h), pg.SRCALPHA) for _ in range(5)]

        self.data = data

        self.reset()

    def reset(self):
        self.dt = 0
        self.passenger_spawn = 0
        self.gui = setup_gui([self.w, self.h])

        data.score = 0
        data.stations = [Station(Shape.CIRCLE, Vector2(125, 100)),
                         Station(Shape.CIRCLE, Vector2(350, 150)),
                         Station(Shape.CIRCLE, Vector2(300, 350)),
                         Station(Shape.CIRCLE, Vector2(600, 650)),
                         Station(Shape.SQUARE, Vector2(400, 250)),
                         Station(Shape.SQUARE, Vector2(500, 500)),
                         Station(Shape.TRIANGLE, Vector2(100, 450)),
                         Station(Shape.TRIANGLE, Vector2(100, 250))]
        data.rails = []
        data.reset_color()
        data.create_rail(self.gui)
        data.create_rail(self.gui)
        data.create_rail(self.gui)

    def play_step(self, action):

        dt = self.dt/1000
        reward, game_over, score = self.update(dt, action)
        self.draw()
        self.dt = self.clock.tick(SPEED)

        return reward, game_over, score

    def update(self, dt, action):

        reward = 0

        # UPDATE GUI
        self.gui.update(dt)
        self.passenger()

        # HANDLE EVENTS
        for event in pg.event.get():
            if self.gui.process_event(event):
                continue
            if event.type == pg.QUIT:
                exit(0)
            elif event.type == SCORE_POINT:
                data.score += 1
                self.gui.set_score(data.score)
                reward = 10
            elif event.type == LOSE_POINT:
                data.score -= 1
                self.gui.set_score(data.score)
                # ? Should we penalise by the same rate that we reward? Probably not
                # ? but I'm not too sure. For now, I set it -10 since we are deducing the score
                # ? by the same rate but the negative reward will probably need to be tweaked
                reward = -10
            elif event.type == TRAIN_STOP:
                self.train_stop(event)

        # GIVEN action, CONDUCT IT :P
        self.do_action(action)

        for r in data.rails:
            r.update(dt, data)

        self.passenger_spawn += dt

        # CHECK IF GAME OVER
        for x in data.stations:
            if x.update():
                # ? Should we penalise at game over?
                reward = -10
                return reward, True, data.score

        return reward, False, data.score

    def do_action(self, action):

        mode, stations, rail = self.interpret_action(action)

        if mode == Mode.DoNothing:
            #print("AI has chosen to do nothing!")
            return
        elif mode == Mode.Connect:
            #print("AI has chosen to connect a segment!")
            self.create_segment(stations, rail)
        elif mode == Mode.Disconnect:
            #print("AI has chosen to disconnect a segment!")
            self.disconnect_segment(stations, rail)

    def interpret_action(self, action):

        # Initialise to interpret action
        mode = None
        s1, s2 = (None, None)
        r = None

        # Split action accordingly
        mode_action = action[:3]
        station_action = action[3:len(data.stations)+3]
        rail_action = action[len(data.stations)+3:len(action)]

        # Interpret mode, if Mode.DoNothing then no need for further interpretation
        if np.array_equal(mode_action, [0, 0, 1]):
            mode = Mode.DoNothing
            return mode, (s1, s2), r
        elif np.array_equal(mode_action, [1, 0, 0]):
            mode = Mode.Connect
        elif np.array_equal(mode_action, [0, 1, 0]):
            mode = Mode.Disconnect

        # Interpret stations
        result = np.where(station_action == 1)
        s1 = result[0][0]
        s2 = result[0][1]

        # Interpret rail
        result = np.where(rail_action == 1)
        r = result[0][0]

        return mode, (s1, s2), r

    def create_segment(self, s, r):
        s1, s2 = s
        stations = (data.stations[s1], data.stations[s2])
        rail = data.rails[r]

        if len(rail.segments) == 0:

            tmp_segment = TrackSegment(rail, stations[0].location, (s1, None))
            tmp_segment.update_dst(data.stations,  s2)
            rail.add_segment(tmp_segment, data.stations)

        else:

            if rail.is_on_rail(s1) and rail.is_on_rail(s2):
                #print("AI has chosen an invalid action!")
                return

            if not rail.is_on_rail(s1) and not rail.is_on_rail(s2):
                #print("AI has chosen an invalid action!")
                return

            start = data.stations[rail.start_station()]
            end = data.stations[rail.end_station()]

            if stations[0] == start or stations[0] == end:

                temp_segment = TrackSegment(rail, stations[0].location, (s1, None))
                temp_segment.update_dst(data.stations,  s2)

                rail.add_segment(temp_segment, data.stations)

            if stations[1] == start or stations[1] == end:

                temp_segment = TrackSegment(rail, stations[1].location, (s2, None))
                temp_segment.update_dst(data.stations,  s1)

                rail.add_segment(temp_segment, data.stations)

    def disconnect_segment(self, station: int, rail: int):
        if data.rails[rail].can_remove_station(station):
            data.rails[rail].remove_station(station)

    def draw(self):

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

    def train_stop(self, event):
        station: Station = data.stations[event.station]
        train: Train = event.train

        for passenger in station.passengers:
            if passenger.should_embark():
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


'''
if __name__ == '__main__':
    game = MiniMetroGameAI()

    while True:
        
        a_0 = np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])
        game_over = game.play_step(a_0)
        game.reset()

        # a_1 = np.array([1,0,0,1,0,1,0,0,0,0,1,0,0])
        # game_over = game.play_step(a_1)

        # a_2 = np.array([1,0,0,0,0,1,1,0,0,0,1,0,0])
        # game_over = game.play_step(a_2)

        # a_3 = np.array([0,1,0,0,0,1,1,0,0,0,1,0,0])
        # game_over = game.play_step(a_3)

        if game_over == True:
            break
        
    #print('Final Score', data.score)
          
    pg.quit()
'''
