import gym
import numpy as np
from pdb import set_trace

env_wrapper = gym.make('TestEnv-v0')
alpha = 0.2 # learning rate
gamma = 0.99 # discounting factor
epsilon = 0.2 # exploration rate

action_space_translate = {0:"show ad", 1:"send award", 2:"increase difficulty", 3:"decrease difficulty"}

# initialise Q with ones
Q = np.ones((env_wrapper.action_space.n, env_wrapper.observation_space.size))
print("initialise Q with ones: ", Q)

def greedy(valid_actions, state):

    values = Q[valid_actions, state]
    print("greedy - values:",values)
    candidates = np.argwhere(values == np.amax(values))
    print("greedy - candidates:",candidates)

    return np.random.choice(valid_actions[candidates.flatten()])


def epsilon_greedy(valid_actions, state, epsilon):

    if np.random.rand() < epsilon:
        print("explore this time..")
        return np.random.choice(valid_actions)

    return greedy(valid_actions, state)


# qlearning of one episode
def qlearning():

    obs = env_wrapper.reset()

    state = env_wrapper.observation_space[obs[0],obs[1],obs[2],obs[3]]

    # the default first engagement: online
    engagement = env_wrapper.env.Engagements.online.name

    for t in range(0,100):
    
        # choose action with epsilon_greedy
        # note that there are limit actions to choose according to current engagement
        action = epsilon_greedy(env_wrapper.env.get_valid_actions(engagement), state, epsilon)

        new_obs, reward, done, info = env_wrapper.step(action)
        new_state = env_wrapper.observation_space[new_obs[0],new_obs[1],new_obs[2],new_obs[3]]

        # here comes a new engagement after the step
        engagement = info['engagement']

        # update Q
        delta = reward + gamma * np.max(Q[:, new_state]) - Q[action, state]
        Q[action, state] += alpha * delta

        print('update Q[', state, ',', env_wrapper.env.Actions(action).name,']:',Q[action, state])

        state = new_state
