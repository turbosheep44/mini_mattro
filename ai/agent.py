from collections import deque

import torch
import torch.nn.functional as F
from torch import optim
import numpy as np

from util import *
from ai import model

MAX_MEMORY = 100_000
MEMORY_THRESHOLD = 1024
BATCH_SIZE = 128

LR = 0.0001
GAMMA = 0.8

EPSILON_INITIAL = 1
EPSILON_FINAL = 0.001
EPSILON_STEPS = 10000

DEVICE: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
RANDOM: np.random.RandomState = np.random.RandomState()


class Agent:

    def __init__(self, state_size, num_actions):
        self._num_actions = num_actions
        self.epsilon = EPSILON_INITIAL
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
        loss = self.loss_func(pred, target)
        loss.backward()
        self.optimizer.step()

        if self._updates % 100 == 0:
            self.loss_values.append(loss.item())
