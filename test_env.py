import logging
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
from enum import Enum
from time import time
from pdb import set_trace

logger = logging.getLogger(__name__)
        

class TestEnv(gym.Env):
    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second': 2
    }

    class States(Enum):
        online_motivation = 0
        ad_acceptance = 1
        mission_skill = 2
        consumption_ability = 3

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

        # online_motivation(0-99), ad_acceptance(0-99), mission_skill(0-99), consumption_ability(0-99)
        x = np.array(np.arange(pow(self.threshold,4)))
        self.observation_space = np.reshape(x,(self.threshold,self.threshold,self.threshold,self.threshold))

        self._seed()
        self.viewer = None
        self.state = None

        self.last_online_time = 0
        self.time_sum = 0
        self.online_time_sum = 0
        self.online_time_percent = 0

        self.engagement_list = list(map(lambda x: x.name, self.Engagements))



    # random seed
    def _seed(self, seed=None):

        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    # reset to initial state
    def _reset(self):
        # set fixed initial values
        middle = int(self.threshold/2)
        self.state = [middle,middle,middle,middle]
        self.last_online_time = time()

        print('initial state:', self.state, self.last_online_time)

        return np.array(self.state)

    # take an action
    def _step(self, action):

        print('send response: ', self.Actions(action).name)

        event = None
        events = {}
        engagement = None
        reward = 0

        while True:

            event = input('Enter the engagement(online/level_up/mission_completed/mission_failed/transaction)\
                 / event(ad_closed/ad_opened/mission_start/offline)')

            if event not in self.engagement_list:
                print('got event:',event)
                events[time()] = event
            else:
                print('got engagement:',event)
                engagement = event
                break

        # -------------------------- deal with events ----------------------------

        # ------- ad -------
        # ad_opened event: reward + 1
        ad_open_times = len(list(filter(lambda x: x =='ad_opened', events.values())))
        # ad_closed event: reward - 1
        ad_close_times = len(list(filter(lambda x: x =='ad_closed', events.values())))

        reward += ad_open_times
        reward -= ad_close_times


        self.state[self.States.ad_acceptance.value] += ad_open_times
        self.state[self.States.ad_acceptance.value] -= ad_close_times
        if self.state[self.States.ad_acceptance.value] > self.threshold:
            self.state[self.States.ad_acceptance.value] = self.threshold
        if self.state[self.States.ad_acceptance.value] < 0:
            self.state[self.States.ad_acceptance.value] = 0


        # -------------------------- deal with the engagement ----------------------------

        # ------- online time -------
        if engagement == self.Engagements.online.name:
            current_time = time()
            last_offline_time = list(filter(lambda x: x[1]==self.Events.offline.name, events.items()))[0][0]

            self.time_sum += (current_time - self.last_online_time)
            self.online_time_sum += (last_offline_time - self.last_online_time)

            current_online_time_percent = self.online_time_sum/self.time_sum * 100

            if self.online_time_percent != 0: # not count into reward at the first time
                reward += (current_online_time_percent - self.online_time_percent)
            self.online_time_percent = current_online_time_percent

            self.state[self.States.online_motivation.value] = int(self.online_time_percent)


        # ------- mission -------
        elif engagement == self.Engagements.mission_completed.name:
            reward += 1
            self.state[self.States.mission_skill.value] += 1
            if self.state[self.States.mission_skill.value] > self.threshold:
                self.state[self.States.mission_skill.value] = self.threshold
            

        elif engagement == self.Engagements.mission_failed.name:
            reward -= 1
            self.state[self.States.mission_skill.value] -= 1
            if self.state[self.States.mission_skill.value] < 0:
                self.state[self.States.mission_skill.value] = 0


        elif engagement == self.Engagements.transaction.name:
            reward += 2
            self.state[self.States.consumption_ability.value] += 1 # should consider about online time
            if self.state[self.States.consumption_ability.value] > self.threshold:
                self.state[self.States.consumption_ability.value] = self.threshold

        if reward != 0:
            print('reward:', reward)

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
            valid_actions = [self.Actions.decrease_difficulty.value, self.Actions.goods_recommend.value]
        elif engagement == self.Engagements.transaction.name:
            valid_actions = [self.Actions.send_award.value, self.Actions.goods_recommend.value]

        return np.array(valid_actions)