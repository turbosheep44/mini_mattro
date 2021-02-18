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

    def __init__(self, simulated_speed: int = 60, normal_speed: bool = False, show_frames: int = 10):
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

        reward -= sum(len(s.passengers) for s in data.stations) * 0.1

    def do_action(self, action):
        if type(action) == type(None):
            return

        mode, stations, rail = self.interpret_action(action)

        if mode == Mode.Connect:
            self.connect(stations[0], stations[1], rail)

        elif mode == Mode.Disconnect:
            self.remove_station(stations[0], rail)

        elif mode == Mode.AddTrain:
            self.add_train(rail)

        elif mode == Mode.UpgradeTrain:
            u_train = data.rails[rail].get_upgradable()
            self.upgrade_train(u_train)

        elif mode == Mode.DeleteTrain:
            alive_trains = [t for t in data.rails[rail].trains if not t.end_of_life]
            if len(alive_trains) > 0:
                random.choice(alive_trains).end_of_life = True

    def interpret_action(self, action):
        # Split action accordingly
        mode_action = action[:6]
        station_action = action[6:len(data.stations)+6]
        rail_action = action[len(data.stations)+6:]

        mode = np.argmax(mode_action)
        stations = np.argwhere(station_action == np.amax(station_action)).flatten()
        rail = np.argmax(rail_action)

        return Mode(mode), stations, rail


def do_action_and_delay(action):
    game.play_step(action)
    for i in range(120):
        game.play_step(None)


if __name__ == '__main__':
    game = MiniMattroAI(60)

    while True:
        game_over, reward = game.play_step(None)
        if game_over == True:
            break

    print('Final Score', data.score)
    pg.quit()

    # create and remove segments
    # do_action_and_delay([0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1])
    # do_action_and_delay([0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1])
    # do_action_and_delay([0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    # do_action_and_delay([0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1])
    # do_action_and_delay([0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    # do_action_and_delay([0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1])

    # delete a train before rail exists
    # do_action_and_delay([0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    # # add train to rail
    # do_action_and_delay([0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])

    # # upgrade train
    # do_action_and_delay([0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    # do_action_and_delay(None)
    # do_action_and_delay([0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    # do_action_and_delay([0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])

    # # remove train
    # do_action_and_delay([0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    # do_action_and_delay([0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    # do_action_and_delay(None)
    # do_action_and_delay(None)
    # do_action_and_delay([0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])

    # # upgrade train
    # do_action_and_delay([0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])
