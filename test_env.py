import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)


        

class TestEnv(gym.Env):
    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second': 2
    }

    class Actions(Enum):
        show_ad = 0
        send_award = 1
        increase_difficulty = 2
        decrease_difficulty = 3
        goods_recommend = 4

    class Engagements(Enum):
        online = 0
        transaction = 1
        mission_completed = 2
        mission_failed = 3
        level_up = 4

    class Events(Enum):
        ad_closed = 0
        ad_opened = 1
        offline = 2
        mission_start = 3

    def __init__(self):

        self.threshold = 100

        # see Actions
        self.action_space = spaces.Discrete(5)

        high = np.array([self.threshold,self.threshold])#, self.threshold, self.threshold, self.threshold])

        # online_motivation(0-99), ad_acceptance(0-99), mission_skill(0-99), consumption_ability(0-99)
        x = np.array(np.arange(100000000))
        self.observation_space = np.reshape(x,(100,100,100,100))

        self._seed()
        self.viewer = None
        self.state = None

        # timestamp of last read event/engagement
        self.last_read_time = 0

        self.engagement_list = list(map(lambda x: x.name, self.Engagements))



    # random seed
    def _seed(self, seed=None):

        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    # reset to initial state
    def _reset(self):
        # set fixed initial values
        self.state = [50,50,50,50]

        print('initial state:', self.state)

        return np.array(self.state)

    # take an action
    def _step(self, action):

        print('send response: ', self.Actions(action).name)
        # read events after last_read_time and record them
        event = None
        events = {}
        engagement = None
        i = 0
        while True:

            event = input('Enter the engagement(online) / event(ad_closed, ad_opened)')

            if event not in self.engagement_list:
                print('got event:',event)
                i += 1
                events[i] = event #keys can be current time or sth..
            else:
                print('got engagement:',event)
                engagement = event
                break

        # ad_opened event: reward + 1
        ad_open_times = len(list(filter(lambda x: x =='ad_opened', events.values())))
        # ad_closed event: reward - 1
        ad_close_times = len(list(filter(lambda x: x =='ad_closed', events.values())))
        
        reward = ad_open_times - ad_close_times

        if reward != 0:
            print('reward:', reward)

        # online engagement: reward + 1, else: reward - 1
        # reward += ((engagement == 'online') and 1 or -1)

        # move to next state
        # update ad_acceptance, online_motivation
        # self.state[0] += online_times - 5
        self.state[1] += ad_open_times
        self.state[1] -= ad_close_times
        
        print('new state:', self.state)

        # returns: observation (object, next_state), reward (float), done (boolean), info (dict)
        return np.array(self.state), reward, False, {"engagement": engagement}


    # not used currently
    def _render(self, mode='human', close=False):
        if close:
            if self.viewer is not None:
                self.viewer.close()
                self.viewer = None
            return

        # screen_width = 600
        # screen_height = 400

        # TODO

        print("action: ", self.action)
        print("state: ", self.state)


    # only some of the actions are valid according to current engagement
    def get_valid_actions(self, engagement):
        valid_actions = []
        if engagement not in self.engagement_list:
            pass
        elif engagement == self.Engagements.online.name:
            valid_actions = [self.Actions.send_award.value, self.Actions.show_ad.value, self.Actions.goods_recommend.value]
        elif engagement == self.Engagements.level_up.name:
            valid_actions = [self.Actions.send_award.value]
        elif engagement == self.Engagements.mission_completed.name:
            valid_actions = [self.Actions.send_award.value, self.Actions.increase_difficulty.value, self.Actions.decrease_difficulty.value]
        elif engagement == self.Engagements.mission_failed.name:
            valid_actions = [self.Actions.increase_difficulty.value, self.Actions.decrease_difficulty.value, self.Actions.goods_recommend.value]
        elif engagement == self.Engagements.transaction.name:
            valid_actions = [self.Actions.send_award.value, self.Actions.goods_recommend.value]

        return np.array(valid_actions)