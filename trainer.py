from util import data
from pdqn_agent import PDQN_Agent
from game_ai import MiniMattroAI

EPISODES = 5000
NUM_PARAMS = [0, 3, 2, 1, 1, 1]
PARAM_CLASSES = [
    # Connect (rail, station, station)
    3, 8, 8,
    # Disconnect (rail, station)
    3, 8,
    # AddTrain (rail)
    3,
    # UpgradeTrain (rail)
    3,
    # DeleteTrain (rail)
    3
]


def train():
    # initalise the environment and the agent
    env = MiniMattroAI(show_frames=60)
    agent = PDQN_Agent(len(env.get_state()), 6, NUM_PARAMS, PARAM_CLASSES)

    episode_rewards = []
    total_reward = 0
    record = 0

    for i in range(EPISODES):
        # reset the game envrionment
        env.reset()

        # get the initial state and action
        state = env.get_state()
        action, params, all_params = agent.act(state)
        episode_reward = 0.0
        game_over = False

        while not game_over:
            # perform the action and identify the reward and resulting state
            game_over, reward = env.play_step(action, params)
            next_state = env.get_state()

            # add this (state + action -> next_state) object to agent memory
            agent.step(state, (action, all_params), reward, next_state, game_over)

            # get next action and update state
            action, params, all_params = agent.act(state)
            state = next_state
            episode_reward += reward

        # decay epsilon
        agent.end_episode()
        if data.score > record:
            record = data.score
        print(f"Game {i:2}   Score {data.score:3}    Record {record}")

        # store rewards for plotting later
        episode_rewards.append(episode_reward)
        total_reward += episode_reward


if __name__ == '__main__':
    train()
