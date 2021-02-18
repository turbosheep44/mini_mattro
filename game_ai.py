from mini_mattro import FPS, MiniMattro
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
    AddTrain = 3
    UpgradeTrain = 4
    DeleteTrain = 5


class MiniMattroAI(MiniMattro):

    def __init__(self, simulated_speed: int = 60, normal_speed: bool = True, show_frames: int = 10):
        super().__init__()
        self.simulated_speed: int = simulated_speed
        self.normal_speed: bool = normal_speed
        self.show_frames: int = show_frames
        self.frames: int = 0
        self.reward: int = 0

    def play_step(self, action):

        dt = 1/self.simulated_speed if not self.normal_speed else self.clock.tick(FPS) / 1000
        self.frames += 1
        self.do_action(action)
        game_over = self.update(dt)

        if self.frames == self.show_frames or self.normal_speed:
            self.draw()
            self.frames = 0

        return game_over, self.reward

    def handle_events(self, events: 'list[Event]') -> None:
        self.reward = 0
        for event in events:
            if event.type == LOSE_POINT:
                self.reward -= 10
            elif event.type == SCORE_POINT:
                self.reward += 1

    def do_action(self, action):
        if type(action) == type(None):
            return

        mode, stations, rail = self.interpret_action(action)

        if mode == Mode.DoNothing:
            #print("AI has chosen to do nothing!")
            return
        elif mode == Mode.Connect:
            #print("AI has chosen to connect a segment!")
            self.connect(stations[0], stations[1], rail)
        elif mode == Mode.Disconnect:
            #print("AI has chosen to disconnect a segment!")
            self.remove_station(stations, rail)

        elif mode == Mode.AddTrain:
            self.add_train(rail)

        elif mode == Mode.UpgradeTrain:
            u_train = data.rails[rail].get_upgradable()
            self.upgrade_train(u_train)

        elif mode == Mode.DeleteTrain:
            if len(data.rails[rail].trains) > 0:
                self.delete_train(random.choice(data.rails[rail].trains))

    def interpret_action(self, action):

        # Initialise to interpret action
        mode = None
        s1, s2 = (None, None)
        r = None

        # Split action accordingly
        mode_action = action[:6]
        station_action = action[6:len(data.stations)+6]
        rail_action = action[len(data.stations)+6:len(action)]

        # Interpret mode, if Mode.DoNothing then no need for further interpretation
        if np.array_equal(mode_action, [0, 0, 1, 0, 0, 0]):
            mode = Mode.DoNothing
            return mode, (s1, s2), r
        elif np.array_equal(mode_action, [1, 0, 0, 0, 0, 0]):
            mode = Mode.Connect
        elif np.array_equal(mode_action, [0, 1, 0, 0, 0, 0]):
            mode = Mode.Disconnect
        elif np.array_equal(mode_action, [0, 0, 0, 1, 0, 0]):
            mode = Mode.AddTrain
        elif np.array_equal(mode_action, [0, 0, 0, 0, 1, 0]):
            mode = Mode.UpgradeTrain
        elif np.array_equal(mode_action, [0, 0, 0, 0, 0, 1]):
            mode = Mode.DeleteTrain

        # Interpret stations
        result = np.where(station_action == 1)
        s1 = result[0][0]
        s2 = result[0][1]

        # Interpret rail
        result = np.where(rail_action == 1)
        r = result[0][0]

        # WORK NEEDED HERE

        return mode, (s1, s2), r


if __name__ == '__main__':
    game = MiniMattroAI(60, True)

    a_0 = np.array([1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    game_over, reward = game.play_step(a_0)

    while True:

        # Connect s1 with s2
        # a_0 = np.array([1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
        game_over, reward = game.play_step(None)

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
