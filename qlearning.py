import numpy as np
from pdb import set_trace
from test_env import *

alpha = 0.2 # learning rate
gamma = 0.99 # discounting factor
epsilon = 0.2 # exploration rate

# initialise Q with ones
Q = np.ones((len(action_space), observation_space.size))

# load Q with existing dump file
# Q = np.load('test1.npy')

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


def step(obs, engagement):
    # choose action with epsilon_greedy
    # note that there are limit actions to choose according to current engagement
    state = observation_space[obs[0],obs[1],obs[2],obs[3]]
    action = epsilon_greedy(get_valid_actions(engagement), state, epsilon)
    print("would take action:", action)
    return action


# qlearning of one episode
def learn(new_obs, reward, last_obs, last_action, is_new_user = False):

    # new user, learn nothing
    if is_new_user:
        return

    new_state = observation_space[new_obs[0],new_obs[1],new_obs[2],new_obs[3]]
    last_state = observation_space[last_obs[0],last_obs[1],last_obs[2],last_obs[3]]
    
    # update Q
    delta = reward + gamma * np.max(Q[:, new_state]) - Q[last_action, last_state]
    Q[last_action, last_state] += alpha * delta

    print('update Q[', last_state, ',', Actions(last_action).name,']:',\
        Q[last_action, last_state])
