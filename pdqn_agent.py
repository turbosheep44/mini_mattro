from copy import deepcopy
from typing import Tuple
import torch
import torch.nn.functional as F
from torch import nn, optim
from torch.autograd import Variable
import numpy as np
from torch.serialization import DEFAULT_PROTOCOL
from memory import Memory

EPSILON_INITAIL: float = 1
EPSILON_FINAL: float = 0.01
EPSILON_STEPS: int = 1000

BATCH_SIZE: int = 64
GAMMA: float = 0.999

MEMORY_SIZE: int = 10_000
INITIAL_MEMORY_THRESHOLD: int = 256

TAU_ACTOR: float = 0.01
TAU_PARAM: float = 0.001
ACTOR_LEARNING_RATE: float = 0.00001
PARAM_LEARNING_RATE: float = 0.000001

DEVICE: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
RANDOM: np.random.RandomState = np.random.RandomState()

HIDDEN_LAYERS = [256, 128, 64]  # [512, 256, 128, 64]
LOSS_FUNC = F.mse_loss


def soft_update_target_network(source_network, target_network, tau):
    for target_param, param in zip(target_network.parameters(), source_network.parameters()):
        target_param.data.copy_(tau * param.data + (1.0 - tau) * target_param.data)


def hard_update_target_network(source_network, target_network):
    for target_param, param in zip(target_network.parameters(), source_network.parameters()):
        target_param.data.copy_(param.data)


class Actor(nn.Module):

    def __init__(self, state_size, action_size, param_classes):
        super().__init__()

        # create layers
        self.layers = nn.ModuleList()
        input_size = state_size + sum(param_classes)

        self.layers.append(nn.Linear(input_size, HIDDEN_LAYERS[0]).to(DEVICE))
        for i in range(1, len(HIDDEN_LAYERS)):
            self.layers.append(nn.Linear(HIDDEN_LAYERS[i - 1], HIDDEN_LAYERS[i]).to(DEVICE))
        last_hidden_size = HIDDEN_LAYERS[-1]
        self.layers.append(nn.Linear(last_hidden_size, action_size).to(DEVICE))

        # initialise layer weights
        for i in range(0, len(self.layers) - 1):
            nn.init.kaiming_normal_(self.layers[i].weight, nonlinearity="relu")
            nn.init.zeros_(self.layers[i].bias)

        nn.init.normal_(self.layers[-1].weight, mean=0., std=0.0001)
        nn.init.zeros_(self.layers[-1].bias)

    def forward(self, state, params):

        x = torch.cat((state, params), dim=-1)
        for layer in self.layers:
            x = F.relu(layer(x))
        return x


class Param(nn.Module):

    def __init__(self, state_size, param_classes):
        super().__init__()

        # create layers
        self.layers = nn.ModuleList()
        input_size = state_size

        self.layers.append(nn.Linear(input_size, HIDDEN_LAYERS[0]).to(DEVICE))
        for i in range(1, len(HIDDEN_LAYERS)):
            self.layers.append(nn.Linear(HIDDEN_LAYERS[i - 1], HIDDEN_LAYERS[i]).to(DEVICE))
        last_hidden_size = HIDDEN_LAYERS[-1]

        self.output_layers = []
        for classes in param_classes:
            self.output_layers.append(nn.Linear(last_hidden_size, classes).to(DEVICE))

        # initialise layer weights
        for i in range(0, len(self.layers)):
            nn.init.kaiming_normal_(self.layers[i].weight, nonlinearity="relu")
            nn.init.zeros_(self.layers[i].bias)

        for output_layer in self.output_layers:
            nn.init.normal_(output_layer.weight, std=0.0001)
            nn.init.zeros_(output_layer.bias)

    def forward(self, state):
        x = state
        num_hidden_layers = len(self.layers)
        for i in range(0, num_hidden_layers):
            x = F.relu(self.layers[i](x))

        outputs = tuple([F.softmax(output_layer(x), dim=-1) for output_layer in self.output_layers])
        return torch.cat(outputs, dim=-1)


class PDQN_Agent(object):

    def __init__(self, state_size, num_actions: int, num_params: 'list[int]', param_classes: 'list[int]'):
        self._epsilon: float = EPSILON_INITAIL
        self._num_actions: int = num_actions
        self._num_params: 'list[int]' = num_params  # number of parameters for each action
        self._total_params: int = np.sum(self._num_params)  # the total number of parameter values
        self._param_classes: 'list[int]' = param_classes  # the number of classes for each parameter
        assert self._total_params == len(self._param_classes)

        self._step: int = 0
        self.updates: int = 0

        # initialise the replay memory, parameter network and actor network
        self.replay_memory = Memory(MEMORY_SIZE, tuple([state_size]), tuple([1+sum(self._num_params)]))

        self.param = Param(state_size,  self._param_classes).to(DEVICE)
        self.param_target = Param(state_size,  self._param_classes).to(DEVICE)
        hard_update_target_network(self.param, self.param_target)
        self.param_target.eval()

        self.actor = Actor(state_size, num_actions, self._param_classes).to(DEVICE)
        self.actor_target = Actor(state_size, num_actions, self._param_classes).to(DEVICE)
        hard_update_target_network(self.actor, self.actor_target)
        self.actor_target.eval()

        # initalise the optimisers for the actor and parameter actor
        self.actor_optimiser = optim.Adam(self.actor.parameters(), lr=ACTOR_LEARNING_RATE)
        self.param_optimiser = optim.Adam(self.param.parameters(), lr=PARAM_LEARNING_RATE)

    def end_episode(self):
        self._epsilon -= (EPSILON_INITAIL - EPSILON_FINAL)/EPSILON_STEPS
        if self._epsilon < EPSILON_FINAL:
            self._epsilon = EPSILON_FINAL

    def act(self, state) -> 'Tuple[int, list[int], list[int]]':
        # set inference only mode for faster computation
        with torch.no_grad():

            # Hausknecht and Stone [2016] use epsilon greedy actions with uniform random action-parameter exploration
            rnd = RANDOM.uniform()
            if rnd < self._epsilon:

                # uniform random action exploration
                action = RANDOM.choice(self._num_actions)
                all_params = np.array([RANDOM.randint(0, class_count) for class_count in self._param_classes])

            else:
                # create state tensor and use networks to get the params and action Q values
                state = torch.from_numpy(state).float().to(DEVICE)
                params = self.param(state)
                Q_a: torch.Tensor = self.actor(state, params)

                # select action with max Q value
                action = torch.argmax(Q_a).item()
                # convert params arrays from 1-hot encoding to class indices
                all_params = np.ones(len(self._param_classes), dtype=int)
                param_data = params.cpu().numpy()
                start: int = 0
                for i, cls in enumerate(self._param_classes):
                    all_params[i] = np.argmax(param_data[start:start+cls])
                    start += cls

            # get the parameters for the chosen action
            offset = sum(self._num_params[:action])
            action_parameters = all_params[offset:offset+self._num_params[action]]

        return action, action_parameters, all_params

    def step(self, state, action, reward, next_state, terminal):
        # store this step in memory
        full_action = np.concatenate(([action[0]], action[1])).ravel()
        self.replay_memory.append(state, full_action, reward, next_state, terminal)

        # if there are enough training examples, do training
        self._step += 1
        if self._step >= BATCH_SIZE and self._step >= INITIAL_MEMORY_THRESHOLD:
            self._optimize_td_loss()
            self.updates += 1

    def _optimize_td_loss(self):
        # get a batch of steps from  memory
        states, full_actions, rewards, next_states, terminals = self.replay_memory.sample(BATCH_SIZE, random_machine=RANDOM)

        # separate the actions from the paramters and put the parameters back in one-hot encoding
        actions = full_actions[:, 0]
        params = full_actions[:, 1:]

        one_hot_params = []
        for param_set in params:
            tmp = tuple([np.zeros(cls, dtype=np.float) for cls in self._param_classes])
            for i, param in enumerate(param_set):
                tmp[i][int(param)] = 1
            one_hot_params.append(torch.cat([torch.from_numpy(t).float().unsqueeze(0) for t in tmp], dim=-1))
        one_hot_params = torch.cat(one_hot_params).to(DEVICE)
        # print(one_hot_params.shape)

        states = torch.from_numpy(states).to(DEVICE)
        actions = torch.from_numpy(actions).to(DEVICE)
        # params = torch.from_numpy(one_hot_params).to(DEVICE)
        rewards = torch.from_numpy(rewards).to(DEVICE).squeeze()
        next_states = torch.from_numpy(next_states).to(DEVICE)
        terminals = torch.from_numpy(terminals).to(DEVICE).squeeze()

        # ---------------------- optimize Q value network ----------------------
        with torch.no_grad():
            # find the value of next_state  -> max_Q(new_state)
            pred_next_action_parameters = self.param_target(next_states)
            pred_Q_a = self.actor_target(next_states, pred_next_action_parameters)
            Qprime = torch.max(pred_Q_a, 1, keepdim=True)[0].squeeze()

            # actual_reward = reward_given + (value_of_next_state * discount_factor)
            target = rewards + (1 - terminals) * GAMMA * Qprime

        # compute the predicted values
        q_values = self.actor(states, one_hot_params)
        y_predicted = q_values.gather(1, actions.view(-1, 1).long()).squeeze()
        y_expected = target
        loss_Q = LOSS_FUNC(y_predicted, y_expected)

        if self.updates % 100 == 0:
            print(torch.mean(loss_Q))

        self.actor_optimiser.zero_grad()
        loss_Q.backward()
        torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 1)
        self.actor_optimiser.step()

        # ---------------------- optimize param network ----------------------
        with torch.no_grad():
            params = self.param(states)
        params.requires_grad = True

        Q: torch.Tensor = self.actor(states, params)
        loss_Q = torch.mean(torch.sum(Q, 1))

        self.actor.zero_grad()
        loss_Q.backward()

        grad = deepcopy(params.grad.data)
        params = self.param(states)
        out = torch.mul(grad, params)

        self.param.zero_grad()
        out.backward(torch.ones(out.shape).to(DEVICE))
        # torch.nn.utils.clip_grad_norm_(self.param.parameters(), 1)
        self.param_optimiser.step()

        # slowly update target networks
        soft_update_target_network(self.actor, self.actor_target, TAU_ACTOR)
        soft_update_target_network(self.param, self.param_target, TAU_PARAM)


# if __name__ == '__main__':
#     input = torch.from_numpy(np.array([np.random.randn(10) for _ in range(5)], copy=True)).float()
#     input = input.to(DEVICE)
#     # input = torch.randn(10).to(DEVICE)
#     param_classes = [5, 2, 3]
#     nn_param = Param(10, param_classes)
#     nn_actor = Actor(10, 2, param_classes)

#     with torch.no_grad():
#         params = nn_param(input)

    # param_data = params.cpu().numpy()
    # all_params = np.zeros(len(param_classes))
    # start = 0
    # for i, cls in enumerate(param_classes):
    #     all_params[i] = np.argmax(param_data[start:start+cls])
    #     start += cls

    # params.requires_grad = True

    # Q = nn_actor(input, params)
    # Q_loss = torch.mean(torch.sum(Q, 1))

    # nn_actor.zero_grad()
    # Q_loss.backward()

    # grad = deepcopy(params.grad.data)
    # params = nn_param(input)
    # out = torch.mul(grad, params)
    # nn_param.zero_grad()
    # out.backward(torch.ones(out.shape).to(DEVICE))
    # print(nn_param.layers[0].weight.grad)

    # qprime = torch.max(action, 1, keepdim=True)[0].squeeze()
    # terminals = torch.from_numpy(np.array([0, 0, 0, 0, 1]))
    # rewards = torch.from_numpy(np.array([1, -1, -10, 2, 1]))

    # print(f"\nchoose action {torch.argmax(action).item()}")
