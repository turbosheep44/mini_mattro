from mini_mattro import FPS, MiniMattro
import random
from pygame.event import Event
from util.gui import *
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
        #     self.reward -= 100

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

        self._calculate_state_penalties()
        return game_over, self.reward

    def handle_events(self, events: 'list[Event]') -> None:
        for event in events:
            if event.type == SCORE_POINT:
                # self.reward += 1
                pass
            elif event.type == PASSENGER_PICKUP:
                self.reward += 0.5

    def _calculate_state_penalties(self) -> None:
        self._penalise_overflowing_stations(10)
        self._reward_passengers_with_path(0.1, -10)
        self._reward_travelling_passengers(1)

    def _penalise_overflowing_stations(self, penalty) -> None:
        """
        penalise when stations are overflowing; the penalty is is proportional to how close the station is to causing game over

        \t `self.reward -= penalty * percent_lost`
        """
        for s in data.stations:
            if s.losing:
                percent_lost = (LOSE_DELAY - s.loseTime) / LOSE_DELAY
                self.reward -= penalty * percent_lost

    def _reward_passengers_with_path(self, reward, penalty):
        """
        add `reward` to the total reward for each passenger at a station who has a path to their destination.
        add `penalty` to the total reward for each passenger at a station with no path to their destination
        """
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
        found_path: bool = None
        for (start, station) in enumerate(data.stations):
            for p in station.passengers:
                visited.clear()
                waiting.clear()
                waiting.append(start)
                found_path = False

                while len(waiting) != 0:
                    current = waiting.pop(0)
                    visited.add(current)

                    # found path to station with correct shape
                    if data.stations[current].shape == p.shape:
                        found_path = True
                        break

                    # add places we can go from this station
                    for nxt in graph[current]:
                        if nxt not in visited and nxt not in waiting:
                            waiting.append(nxt)

                # reward of penalise based on whether a path was found
                self.reward += (reward if found_path else penalty)

    def _reward_travelling_passengers(self, reward):
        """
        adds `reward` to the total reward for each passenger on a train
        """
        for train in data.trains():
            self.reward += reward * len(train.passengers)

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
        return np.concatenate([self._get_rails_state(), self._get_stations_state(), self._get_train_state()])

    def _one_hot_array(self, classes: int, active: int):
        """
        create a one-hot encoded numpy array for a given number of classes with the given class active

            - `_one_hot_array(4, 3) == [0, 0, 0, 1]`
            - `_one_hot_array(8, 2) == [0, 0, 1, 0, 0, 0, 0, 0]`
        """
        arr = np.zeros(classes)
        arr[active] = 1
        return arr

    def _get_train_state(self):
        trains = []
        for t in data.trains():

            # one-hot encode the passengers in the form [SQUARE, CIRCLE, TRIANGLE, EMTPY]
            passengers = []
            for p in t.passengers:
                passengers.append(self._one_hot_array(4, p.shape.value))

            # pad to 6 passengers with empty passenger shapes
            while len(passengers) < 6:
                passengers.append(self._one_hot_array(4, 3))
            passengers = np.concatenate(passengers)

            # indicate which rail this passenger is on
            rail = self._one_hot_array(4, data.rails.index(t.current_segment.rail))

            # speedy?
            upgrade = t.is_upgraded

            # current location
            from_station = self._one_hot_array(len(data.stations)+1, t.origin())
            to_station = self._one_hot_array(len(data.stations)+1, t.destination())
            amount_traversed = t.position if t.direction == 1 else (1-t.position)

            trains.append(np.concatenate((rail, passengers, upgrade, from_station, to_station, amount_traversed), axis=None))

        # pad until 5 trains
        no_rail = self._one_hot_array(4, 3)
        no_passenger = self._one_hot_array(4, 3)
        from_to = self._one_hot_array(len(data.stations)+1, len(data.stations))
        while len(trains) < 5:
            trains.append(np.concatenate((no_rail, np.concatenate([no_passenger for _ in range(6)]), False, from_to, from_to, 0), axis=None))

        assert len(trains) == 5
        return np.concatenate(trains).ravel()

    def _get_stations_state(self):
        stations = []
        for s in data.stations:
            # the shape of this station
            shape = self._one_hot_array(3, s.shape.value)

            # one-hot encode up to 6 passengers
            temp = s.passengers
            if len(s.passengers) > 6:
                temp = s.passengers[:6]
            passengers = []
            for p in temp:
                passengers.append(self._one_hot_array(4, p.shape.value))
            while len(passengers) < 6:
                passengers.append(self._one_hot_array(4, 3))
            passengers = np.concatenate(passengers)

            # normalised distances to other stations
            distances = []
            for n in data.stations:
                distances.append(s.location.distance_to(n.location))
            largest = np.max(distances)
            distances[:] = np.array([d/largest for d in distances])

            # how close this station is to losing
            percent_lost = ((LOSE_DELAY - s.loseTime) / LOSE_DELAY) if s.losing else 0

            stations.append(np.concatenate([shape, passengers, distances, percent_lost], axis=None))

        assert len(stations) == len(data.stations)
        return np.concatenate(stations).ravel()

    def _get_rails_state(self):

        number_of_stations = len(data.stations)
        state = np.zeros((3, number_of_stations, (number_of_stations+1)))

        for rail_counter, rail in enumerate(data.rails):

            segment_counter = 0
            last = 0

            if len(rail.segments) > 0:
                for segment_counter, segment in enumerate(rail.segments):
                    if len(segment.stations) > 0:
                        state[rail_counter, segment_counter, segment.stations[0]] = 1
                        last = segment.stations[1]

                state[rail_counter, segment_counter+1, last] = 1
                segment_counter += 2

            i = number_of_stations
            while i > segment_counter:
                state[rail_counter, i-1, -1] = 1
                i -= 1

        return state.ravel()


if __name__ == '__main__':
    env = MiniMattroAI(normal_speed=True, show_frames=1)
    env.play_step(1, (1, 0, 7))
    env.play_step(1, (0, 0, 4))
    # print(env.get_state())
    # print(env.get_state().shape)
    # env.play_step(4, [1])
    # print(env.get_state())

    while True:
        env.play_step(None, None)
