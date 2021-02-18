from mini_mattro import MiniMattro
import pygame as pg
import random
from pygame.constants import K_SPACE
from pygame.event import Event
from util.gui import *
from entities import TrackSegment, Station, Train
from util import *
from util.gui import setup_gui
import numpy as np
import enum


class Mode(enum.Enum):
    DoNothing = 0
    Connect = 1
    Disconnect = 2


class MiniMattroAI(MiniMattro):

    def __init__(self, simulated_speed: int):
        super().__init__()
        self.simulated_speed: int = simulated_speed
        self.frames = 0
        self.tmp_segment: TrackSegment = None

    def play_step(self, action):

        dt = 1/self.simulated_speed
        self.frames += 1
        self.do_action(action)
        game_over = self.update(dt)

        if self.frames == 10:
            self.draw()
            self.frames = 0

        return game_over

    def handle_events(self, events: 'list[Event]') -> None:
        pass

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


if __name__ == '__main__':
    game = MiniMattroAI(60)

    while True:

        a_0 = np.array([1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])
        game_over = game.play_step(None)

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