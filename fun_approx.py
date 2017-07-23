import numpy as np
from pdb import set_trace
from test_env import *
from manage import *
import logging

alpha = 0.2 # learning rate
gamma = 0.99 # discounting factor
epsilon = 0.2 # exploration rate

num_features = 9

# load theta with existing dump file
theta = load_latest_theta()
print("load latest theta: ", theta)

if not theta:
    # Intialise theta optimistically with small positive values
    theta = 0.1 * np.ones((num_features + 1, 1))


def greedy(valid_actions, state):

    print("greedy - valid_actions:", list(map(lambda x:Actions(x).name, valid_actions)))

    return argmaxQs(state, valid_actions)


def epsilon_greedy(valid_actions, state, epsilon):

    if np.random.rand() < epsilon:
        
        print("epsilon_greedy - explore this time..")

        # TODO set probability from Q
        values = Qs(state, valid_actions)
        probs = np.exp(values) / np.sum(np.exp(values))

        return np.random.choice(valid_actions, p=probs)

    return greedy(valid_actions, state)


def step(obs, engagement):
    # choose action with epsilon_greedy
    # note that there are limit actions to choose according to current engagement
    state = observation_space[obs[0],obs[1],obs[2],obs[3]]
    action = epsilon_greedy(get_valid_actions(engagement), state, epsilon)
    print("would take action:", Actions(action).name)
    return action


# function approximation of one episode
def learn(new_obs, reward, last_obs, last_action, is_new_user = False):

    # new user, learn nothing
    if is_new_user:
        return

    new_state = observation_space[new_obs[0],new_obs[1],new_obs[2],new_obs[3]]
    last_state = observation_space[last_obs[0],last_obs[1],last_obs[2],last_obs[3]]
    
    # update theta
    Qsa = Q(last_state, last_action)
    maxQ = maxQs(new_state)
    error = reward + gamma * maxQ - Qsa
    grad = gradQ(last_state, last_action)
    theta = theta + alpha * error * grad

    print('update theta[', last_state, ',', Actions(last_action).name,']:',\
        theta)


def features(state, action):
    (o_m, a_a, m_s, c_a) = state

    # Initialise the features vector to 0s
    features = np.zeros(num_features + 1)

    # TODO definition of features


def Q(s, a):
        return np.asscalar(np.dot(features(s, a), theta))

def gradQ(s, a):
    return features(s, a).reshape(num_features + 1, 1)

def Qs(s, valid_actions):
    return np.asarray(
        map(lambda a: Q(s, a), valid_actions))

def maxQs(s, valid_actions):
    return np.max(Qs(s, valid_actions))

def argmaxQs(s, valid_actions):
    return valid_actions[np.argmax(Qs(s, valid_actions))]