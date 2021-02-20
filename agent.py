from typing import Tuple
import torch
import numpy as np
from collections import deque

import matplotlib.pyplot as plt
from torch import optim
import torch.nn.functional as F
from game_ai import MiniMattroAI, Mode
from util import *
from ai import model
from util.data import data

MAX_MEMORY = 100_000
MEMORY_THRESHOLD = 1024
BATCH_SIZE = 128

LR = 0.0001
GAMMA = 0.9

EPSILON_INITIAL = 1
EPSILON_FINAL = 0.001
EPSILON_STEPS = 5000

DEVICE: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
RANDOM: np.random.RandomState = np.random.RandomState()
ACTIONS: 'list[Tuple[int, Tuple]]' = []


class Agent:

    def __init__(self, state_size, num_actions):
        self._num_actions = num_actions
        self.epsilon = EPSILON_INITIAL
        self._steps = 0
        self._updates = 0
        self.loss_values = []

        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = model.QValueModel(state_size, num_actions, DEVICE)
        self.optimizer = optim.SGD(self.model.parameters(), lr=LR, momentum=0.8, weight_decay=4e-3)
        self.loss_func = F.mse_loss

    def step(self, state, action, reward, next_state, game_over):
        # put this step in memory
        self.memory.append((state, action, reward, next_state, game_over))

        # dont start training until there are enough steps for a batch
        if len(self.memory) < BATCH_SIZE or len(self.memory) < MEMORY_THRESHOLD:
            return

        # only train every BATCH_SIZE/20 steps
        self._steps += 1
        if self._steps < BATCH_SIZE/20:
            return
        self._steps = 0
        self._updates += 1

        # sample memory
        sample = RANDOM.choice(range(len(self.memory)), size=BATCH_SIZE, replace=False)
        states, actions, rewards, next_states, dones = zip(*[self.memory[el] for el in sample])
        self.train_step(states, actions, rewards, next_states, dones)

    def end_episode(self):
        self.epsilon -= (EPSILON_INITIAL - EPSILON_FINAL)/EPSILON_STEPS
        self.epsilon = max(self.epsilon, EPSILON_FINAL)

    def act(self, state) -> np.ndarray:

        if RANDOM.uniform() < self.epsilon:
            actions = np.zeros(self._num_actions)
            actions[RANDOM.choice(self._num_actions)] = 1
            return actions
        else:
            state = torch.tensor(state, dtype=torch.float).to(DEVICE)
            return self.model(state).detach().cpu().numpy()

    def train_step(self, state, action, reward, next_state, done):
        # convert to tensors
        state = torch.tensor(state, dtype=torch.float).to(DEVICE)
        next_state = torch.tensor(next_state, dtype=torch.float).to(DEVICE)
        action = torch.tensor(action).to(DEVICE)
        reward = torch.tensor(reward, dtype=torch.float).to(DEVICE)

        # predicted Q values with current state
        pred = self.model(state)

        # actual Q value = reward + (discount * maxQ(next_state))
        target = pred.clone()
        for idx in range(len(done)):
            Q_new = reward[idx]
            if not done[idx]:
                Q_new = reward[idx] + (GAMMA * torch.max(self.model(next_state[idx])))

            target[idx][torch.argmax(action[idx]).item()] = Q_new

        # calculate loss over the batch and weight gradients then optimise
        self.optimizer.zero_grad()
        loss = self.loss_func(target, pred)
        loss.backward()
        self.optimizer.step()

        if self._updates % 100 == 0:
            self.loss_values.append(loss.item())


def plot_loss(agent):
    plt.clf()
    plt.title(f'Loss\n' +
              f'batch={BATCH_SIZE} epsilon_initail={EPSILON_INITIAL} epsilon_final={EPSILON_FINAL} epsilon_steps={EPSILON_STEPS}\n' +
              f'gamma={GAMMA} learning_rate={LR} optimiser={type(agent.optimizer).__name__} loss_func={agent.loss_func.__name__}')
    plt.xlabel('Training steps x100')
    plt.ylabel('Loss')
    plt.plot(agent.loss_values)
    plt.show(block=False)
    plt.pause(.001)


def train(model, load=False):
    # init envrionment and agent
    env = MiniMattroAI(show_frames=10000, frames_per_step=60)
    agent = Agent(len(env.get_state()), len(ACTIONS))

    if load == True:
        agent.model.load_state_dict(torch.load(f"model/{model}.pth"))

    record = 0
    for i in range(EPSILON_STEPS+100):
        # reset the game envrionment
        env.reset()

        # get the initial state and action
        state = env.get_state()
        action_q_values = agent.act(state)
        game_over = False

        while not game_over:
            # perform the action and identify the reward and resulting state
            action, params = ACTIONS[np.argmax(action_q_values)]
            game_over, reward = env.play_step(action, params)
            next_state = env.get_state()

            # add this (state + action -> next_state) object to agent memory
            agent.step(state, action_q_values, reward, next_state, game_over)

            # get update state and get next action
            state = next_state
            action_q_values = agent.act(state)

        # decay epsilon
        agent.end_episode()
        if data.score > record:
            record = data.score
        print(f"{i:4})  -> {data.score:3} | {record:3}")
        plot_loss(agent)

    agent.model.save(file_name=f"model/{model}.py")


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
            print('Game', agent.n_games, 'Score',
                  super_cool_score_probably_winning, 'Record:', record)


def populate_actions():
    # one action for 'do nothing'
    ACTIONS.append((Mode.DoNothing.value, None))

    # for each of 3 rails
    for rail in range(3):
        # add, remove and upgrade
        ACTIONS.append((Mode.AddTrain.value, (rail,)))
        ACTIONS.append((Mode.DeleteTrain.value, (rail,)))
        ACTIONS.append((Mode.UpgradeTrain.value, (rail,)))

        for station in range(8):
            # disconnect any one of the stations
            ACTIONS.append((Mode.Disconnect.value, (rail, station)))

            # connect any 2 stations
            for other in range(station + 1, 8):
                ACTIONS.append((Mode.Connect.value, (rail, station, other)))


if __name__ == '__main__':
    populate_actions()
    train(model="model", load=False)
