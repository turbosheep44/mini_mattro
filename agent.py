import torch
import random
import numpy as np
from collections import deque
from game_ai import MiniMattroAI
from util import *
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
        self.distance_state = []

    def get_state(self):

        state = self.get_rails_state() + self.get_distance_state() + self.get_passenger_state()

        return np.array(state, dtype=int)

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
        if self.distance_state != []:
            return self.distance_state

        C = list(itertools.combinations(data.stations, 2))
        distance_state = []

        for c in C:
            distance_state.append(int(math.sqrt((c[0].location.x - c[1].location.x)**2 + (c[0].location.y-c[1].location.y)**2)))

        self.distance_state = distance_state
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

    def get_station_rail_actions(self, mode, prediction=None):
        station_action = [0] * 8
        rail_action = [0] * 3

        if prediction != None:
            station_prediction = prediction[6:len(self.data.stations)+6]
            rail_prediction = prediction[len(self.data.stations)+6:len(prediction)]

        if mode == 0:
            return station_action, rail_action
        elif mode == 1:
            if prediction == None:
                s1, s2 = random.sample(range(8), 2)
                station_action[s1] = 1
                station_action[s2] = 1
            else:
                stations = torch.topk(station_prediction, k=2)[1]
                s1 = stations[0].item()
                s2 = stations[1].item()
                station_action[s1] = 1
                station_action[s2] = 1
        elif mode == 2:
            if prediction == None:
                s1 = random.randint(0, 7)
                station_action[s1] = 1
            else:
                s1 = torch.argmax(station_prediction).item()
                station_action[s1] = 1

        if prediction == None:
            r = random.randint(0, 2)
            rail_action[r] = 1
        else:
            r = torch.argmax(rail_prediction).item()
            rail_action[r] = 1

        return station_action, rail_action

    def get_action(self, state, train = True):
        self.epsilon = GAME_COUNT - self.n_games
        mode_action = [0] * 6

        if random.randint(0, 200) < self.epsilon or train:
            mode = random.randint(0, 5)
            mode_action[mode] = 1

            station_action, rail_action = self.get_station_rail_actions(mode)

        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)

            mode_prediction = prediction[:6]
            mode = torch.argmax(mode_prediction).item()
            mode_action[mode] = 1

            station_action, rail_action = self.get_station_rail_actions(mode, prediction)

        return np.array(mode_action + station_action + rail_action)


def train(model, load = False):
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    game = MiniMattroAI(show_frames=10)
    agent = Agent(data)
    
    if load == True:
        agent.model.load_state_dict(torch.load(f"model/{model}.pth"))

    while True:

        state_old = agent.get_state()
        action = agent.get_action(state_old)
        done, reward = game.play_step(action)
        state_new = agent.get_state()
        agent.train_short_memory(state_old, action, reward, state_new, done)
        agent.remember(state_old, action, reward, state_new, done)

        steps_without_action = 0
        while not done and steps_without_action < 59:
            done, _ = game.play_step(None)
            steps_without_action += 1

        if done:
            super_cool_score_probably_winning = data.score
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if super_cool_score_probably_winning > record:
                record = super_cool_score_probably_winning
                agent.model.save(file_name=f'{model}.pth')

            print('Game', agent.n_games, 'Score', super_cool_score_probably_winning, 'Record:', record)

            plot_scores.append(super_cool_score_probably_winning)
            total_score += super_cool_score_probably_winning
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            helper.plot(plot_scores, plot_mean_scores, model=model)

def test(model):
    agent = Agent(data)
    game = MiniMattroAI(show_frames=10)     
    agent.model.load_state_dict(torch.load(f"model/{model}.pth"))
    record = 0

    while True:
        state_old = agent.get_state()
        action = agent.get_action(state_old, train=False)
        done, reward = game.play_step(action)

        steps_without_action = 0
        while not done and steps_without_action < 59:
            done, _ = game.play_step(None)
            steps_without_action += 1

        if done:
            super_cool_score_probably_winning = data.score
            game.reset()
            agent.n_games += 1

            if super_cool_score_probably_winning > record:
                record = super_cool_score_probably_winning
            print('Game', agent.n_games, 'Score', super_cool_score_probably_winning, 'Record:', record)


if __name__ == '__main__':
    # Train from beginning, save as model1.pth
    train(model = "model1", load = False)

    # Train from loaded model, load from model1.pth
    #train(model = "model1", load = True)

    # Test loaded model, load from model1.pth
    #test(model = "model1")
