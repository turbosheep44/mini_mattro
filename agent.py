import torch
import random
import numpy as np
from collections import deque
from game_ai import MiniMattroAI
from ai import model
from ai import helper
from util.data import data
import itertools
import math

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001
GAME_COUNT = 80


class Agent:

    def __init__(self, data):
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = 0.9  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()
        self.model = model.Linear_QNet(136, 256, 17)
        self.trainer = model.QTrainer(self.model, lr=LR, gamma=self.gamma)
        self.data = data
        self.distance_state = self.get_distance_state()

    # TODO: NEED TO IMPLEMENT
    def get_state(self):

        state = self.get_rails_state() + self.distance_state + self.get_passenger_state()

        return np.array(state, dtype=int)

        # RETURNS NUMBER OF PASSENGERS BY SHAPE AT EVERY STATION

    def get_passenger_state(self):
        p_states = []
        for s in self.data.stations:
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
        C = list(itertools.combinations(self.data.stations, 2))
        distance_state = []

        for c in C:
            distance_state.append(int(math.sqrt((c[0].location.x - c[1].location.x)**2 + (c[0].location.y-c[1].location.y)**2)))

        return distance_state

    def get_rails_state(self):

        number_of_stations = len(data.stations)
        state = np.zeros((number_of_stations, number_of_stations, 3), dtype=bool)

        for current_rail, rail in enumerate(data.rails):
            for segment in rail.segments:

                beginning = segment.stations[0]
                end = segment.stations[1]
                state[beginning, end, current_rail] = True
                state[end, beginning, current_rail] = True

        final_rails_state = []
        for i in range(number_of_stations-1):
            final_rails_state = final_rails_state + state[i][(-((number_of_stations) - (i+1))):].flatten().tolist()

        return final_rails_state

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)
    
    def get_action_two(self,mode,random = False):
        station_action = [0] * 8
        rail_action = [0] * 3
        
        if mode == 0:
            return station_action, rail_action
        elif mode == 1:
            if random:
               s_sample = random.sample(range(8), 1)
            return 


    # * SHOULD BE OK
    def get_action(self, state):
        self.epsilon = GAME_COUNT - self.n_games

        if random.randint(0, 200) < self.epsilon:
            mode = random.randint(0, 4)
            mode_action[mode] = 1

            if mode == 2:
                s_sample = random.sample(range(8), 1)
                s1 = s_sample[0]
                station_action[s1] = 1

            s_sample = random.sample(range(8), 2)
            s1 = s_sample[0]
            s2 = s_sample[1]
            station_action[s1] = 1
            station_action[s2] = 1

            rail = random.randint(0, 2)
            rail_action[rail] = 1

        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            print(prediction.data)
            mode_prediction = prediction[:6]
            station_prediction = prediction[6:len(self.data.stations)+6]
            rail_prediction = prediction[len(self.data.stations)+6:len(prediction)]

            mode = torch.argmax(mode_prediction).item()
            mode_action[mode] = 1

            stations = torch.topk(station_prediction, k=2)[1]
            s1 = stations[0].item()
            s2 = stations[1].item()
            station_action[s1] = 1
            station_action[s2] = 1

            rail = torch.argmax(rail_prediction).item()
            rail_action[rail] = 1

        return np.array(mode_action + station_action + rail_action)


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    game = MiniMattroAI()
    agent = Agent(data)
    while True:
        # get old state
        state_old = agent.get_state()

        # get move
        action = agent.get_action(state_old)

        # perform move and get new state
        # print(action)
        done, reward = game.play_step(action)
        state_new = agent.get_state()

        # train short memory
        agent.train_short_memory(state_old, action, reward, state_new, done)

        # remember
        agent.remember(state_old, action, reward, state_new, done)

        if done:
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if data.score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', data.score, 'Record:', record)

            plot_scores.append(data.score)
            total_score += data.score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            helper.plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()
