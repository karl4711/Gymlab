
import gym
import numpy as np

env = gym.make('TestEnv-v0')
alpha = 0.5 # learning rate
gamma = 0.99 # discounting factor
epsilon = 0.2 # exploration rate

action_space_translate = {0:"show ad", 1:"send award", 2:"increase difficulty", 3:"decrease difficulty"}

# initialise Q with ones
Q = np.ones((env.action_space.n, env.observation_space.size))
print("initialise Q with ones: ", Q)

def greedy(Q, state):
    values = Q[:, state]
    candidates = np.argwhere(values == np.amax(values))
    return np.random.choice(candidates.flatten())


def epsilon_greedy(Q, state, epsilon):
    values = Q[:, state]

    if np.random.rand() < epsilon:
        print("explore this time..")
        return np.random.randint(low=0, high=values.shape[0])

    return greedy(Q, state)


# qlearning of one episode
def qlearning():

    obs = env.reset()
    state = env.observation_space[obs[0],obs[1]]

    for t in range(0,100):
    
        # choose action with epsilon_greedy
        action = epsilon_greedy(Q, state, epsilon)

        new_obs, reward, done, _ = env.step(action)
        new_state = env.observation_space[new_obs[0],new_obs[1]]

        # update Q
        delta = reward + gamma * np.max(Q[:, new_state]) - Q[action, state]
        Q[action, state] += alpha * delta

        print('update Q[', state, ',', action_space_translate[action],']:',Q[action, state])

        state = new_state
