import gym
import numpy as np
from pdb import set_trace

env_wrapper = gym.make('TestEnv-v0')
alpha = 0.2 # learning rate
gamma = 0.99 # discounting factor
epsilon = 0.2 # exploration rate

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

    userid, engagement = env_wrapper.reset()

    state = env_wrapper.observation_space[50,50,50,50]

    for t in range(0,100):
    
        # choose action with epsilon_greedy
        # note that there are limit actions to choose according to current engagement
        action = epsilon_greedy(env_wrapper.env.get_valid_actions(engagement), state, epsilon)
        print("would take action:", action)

        # action(numpy.int32) need to transfer to python int to insert into database
        new_obs, reward, done, info = env_wrapper.step((userid, int(action)))

        # here comes a new engagement after the step
        engagement = info.get('engagement')
        last_state_and_action = info.get('last_state_and_action')
        is_new_user = info.get('is_new_user')
        userid = info.get('userid')

        # new user, learn nothing
        if is_new_user:
            continue

        new_state = env_wrapper.observation_space[new_obs[0],new_obs[1],new_obs[2],new_obs[3]]

        
        last_state = env_wrapper.observation_space[last_state_and_action[2],\
            last_state_and_action[3],last_state_and_action[4],last_state_and_action[5]]
        last_action =  last_state_and_action[6]

        # update Q
        delta = reward + gamma * np.max(Q[:, new_state]) - Q[last_action, last_state]
        Q[last_action, last_state] += alpha * delta

        print('update Q[', last_state, ',', env_wrapper.env.Actions(last_action).name,']:',\
            Q[last_action, last_state])
