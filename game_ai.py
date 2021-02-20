from mini_mattro import FPS, MiniMattro
import pygame as pg
import random
from pygame.constants import K_SPACE
from pygame.event import Event
from util.gui import *
from util import *
from util.gui import setup_gui
import numpy as np
import enum
import itertools
from math import sqrt


class Mode(enum.Enum):
    DoNothing = 0
    Connect = 1
    Disconnect = 2
    AddTrain = 3
    UpgradeTrain = 4
    DeleteTrain = 5


class MiniMattroAI(MiniMattro):

    def __init__(self, simulated_speed: int = 60, normal_speed: bool = False, show_frames: int = 10, frames_per_step: int = 20):
        super().__init__()
        self.frames_per_step: int = frames_per_step
        self.simulated_speed: int = simulated_speed
        self.normal_speed: bool = normal_speed
        self.show_frames: int = show_frames
        self.frames: int = 0
        self.reward: int = 0

        self.distance_state = []

    def play_step(self, action, params):

        # reset the reward for this step and perform the action
        self.reward = 0
        action_valid = self.do_action(action, params)
        # penalise heavily for actions which are not valid
        # if not action_valid:
        # self.reward -= 100

        # play up to n frames
        for _ in range(self.frames_per_step):
            dt = 1 / self.simulated_speed if not self.normal_speed else self.clock.tick(FPS) / 1000
            self.frames += 1
            game_over = self.update(dt)

            # draw only some of the frames
            if self.frames == self.show_frames or self.normal_speed:
                self.draw()
                self.frames = 0

            # dont finish the step frames if the player has lost
            if game_over:
                break

        self.calculate_state_penalties()
        return game_over, self.reward

    def handle_events(self, events: 'list[Event]') -> None:
        for event in events:
            if event.type == SCORE_POINT:
                self.reward += 1

    def calculate_state_penalties(self) -> None:
        # penalise when stations are overflowing and for every person waiting
        for s in data.stations:
            if s.losing:
                self.reward -= 10
            self.reward -= 0.1 * len(s.passengers)

        graph = [set() for _ in data.stations]
        for rail in data.rails:
            for segment in rail.segments:
                to, frm = segment.stations
                graph[to].add(frm)
                graph[frm].add(to)

        # if a passenger has a path to their destination, then reward the AI
        # bfs to see if it is possible to deliver each passenger
        visited = set()
        waiting: 'list[int]' = []
        for (start, station) in enumerate(data.stations):
            for p in station.passengers:
                visited.clear()
                waiting.clear()
                waiting.append(start)

                while len(waiting) != 0:
                    current = waiting.pop(0)
                    visited.add(current)

                    # found path to station with correct shape
                    if data.stations[current].shape == p.shape:
                        self.reward += 0.1
                        break

                    # add places we can go from this station
                    for nxt in graph[current]:
                        if nxt not in visited and nxt not in waiting:
                            waiting.append(nxt)

        # reward for each travelling passenger
        for rail in data.rails:
            for train in rail.trains:
                self.reward += 0.1 * len(train.passengers)

    def do_action(self, action, params) -> bool:
        if type(action) == type(None):
            return True

        mode = Mode(action)

        if mode == Mode.Connect:
            assert len(params) == 3
            return self.connect(params[1], params[2], params[0])

        elif mode == Mode.Disconnect:
            assert len(params) == 2
            return self.remove_station(params[1], params[0])

        elif mode == Mode.AddTrain:
            assert len(params) == 1
            return self.add_train(params[0])

        elif mode == Mode.UpgradeTrain:
            assert len(params) == 1
            u_train = data.rails[params[0]].get_upgradable()
            return self.upgrade_train(u_train)

        elif mode == Mode.DeleteTrain:
            assert len(params) == 1
            alive_trains = [t for t in data.rails[params[0]].trains if not t.end_of_life]
            if len(alive_trains) > 0:
                random.choice(alive_trains).end_of_life = True
                return True
            return False

    def interpret_action(self, action):
        # Split action accordingly
        mode_action = action[:6]
        station_action = action[6:len(data.stations)+6]
        rail_action = action[len(data.stations)+6:]

        mode = np.argmax(mode_action)
        stations = np.argwhere(
            station_action == np.amax(station_action)).flatten()
        rail = np.argmax(rail_action)

        return Mode(mode), stations, rail

    def get_state(self):
        state = self.get_rails_state() +  \
            self.get_passenger_state() + self.get_train_state()
        return np.array(state, dtype=int)

    def get_train_state(self):
        train_state = [data.available_trains, data.available_train_upgrades]
        for rail in data.rails:
            train_state += [
                len(rail.trains),
                sum(1 for train in rail.trains if train.is_upgraded),
                sum(1 for train in rail.trains if train.end_of_life)
            ]
        return train_state

    def get_passenger_state(self):
        p_states = []
        for s in data.stations:
            temp = [0, 0, 0]
            for p in s.passengers:
                if p.shape == Shape.CIRCLE:
                    temp[0] += 1
                elif p.shape == Shape.SQUARE:
                    temp[1] += 1
                else:
                    temp[2] += 1
            p_states.append(temp)
        return np.concatenate(p_states).ravel().tolist()

    def get_distance_state(self):
        if self.distance_state != []:
            return self.distance_state

        combinations = list(itertools.combinations(data.stations, 2))
        distance_state = []

        for c in combinations:
            distance_state.append(int(sqrt(
                (c[0].location.x - c[1].location.x)**2 + (c[0].location.y-c[1].location.y)**2)))

        self.distance_state = distance_state
        return distance_state

    def get_rails_state(self):

        number_of_stations = len(data.stations)
        state = np.zeros(
            (number_of_stations, number_of_stations, 3), dtype=bool)

        for current_rail, rail in enumerate(data.rails):
            for segment in rail.segments:

                beginning = segment.stations[0]
                end = segment.stations[1]
                state[beginning, end, current_rail] = True
                state[end, beginning, current_rail] = True

        final_rails_state = []
        for i in range(number_of_stations-1):
            final_rails_state = final_rails_state + \
                state[i][(-((number_of_stations) - (i+1))):].flatten().tolist()

        return final_rails_state


if __name__ == '__main__':
    env = MiniMattroAI(normal_speed=True, show_frames=1)
    env.play_step(1, (1, 0, 7))
    env.play_step(1, (0, 0, 4))
    print(env.get_state())
    # env.play_step(4, [1])
    # print(env.get_state())

    while True:
        env.play_step(None, None)
