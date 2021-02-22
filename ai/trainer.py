import torch
import numpy as np
from ai.agent import Agent, BATCH_SIZE, EPSILON_FINAL, EPSILON_INITIAL, EPSILON_STEPS, GAMMA, LR

import matplotlib.pyplot as plt
from typing import Tuple

from game_ai import MiniMattroAI, Mode
from util import data

ACTIONS: 'list[Tuple[int, Tuple]]' = []


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
    plt.savefig("plots/plot.png")


def train(model, load=False):
    # init envrionment and agent
    populate_actions()
    env = MiniMattroAI(show_frames=100_000, frames_per_step=60)
    agent = Agent(len(env.get_state()), len(ACTIONS))

    if load == True:
        agent.model.load_state_dict(torch.load(f"{model}.pth"))

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

    agent.model.save(file_name=f"{model}.py")


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
    # start with empty list
    ACTIONS.clear()

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
    train(model="model", load=False)
