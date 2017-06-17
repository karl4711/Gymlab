import logging
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
from enum import Enum
from time import time
import sqlite3
from pdb import set_trace

logger = logging.getLogger(__name__)

sqlite_db = 'test.db'    

state_threshold = 100    

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

        # see Actions
        self.action_space = spaces.Discrete(5)

        # online_motivation(0-99), ad_acceptance(0-99), mission_skill(0-99), consumption_ability(0-99)
        x = np.array(np.arange(pow(state_threshold,4)))
        self.observation_space = np.reshape(x,(state_threshold,state_threshold,state_threshold,state_threshold))

        self._seed()
        self.viewer = None

        self.engagement_list = list(map(lambda x: x.name, self.Engagements))

    # random seed
    def _seed(self, seed=None):

        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    # reset to initial state
    def _reset(self):
        return self.receive_events()

    # keep receiving events and save them, until got an engagement
    def receive_events(self):
        while True:

            userid = input('Enter the userid:')
            event = input('Enter the engagement(online/level_up/mission_completed/mission_failed/transaction)\
                 / event(ad_closed/ad_opened/mission_start/offline):')

            # TODO may save userids in memory 
            if not query_state(userid):
                print("user not exist, initialise here.", userid)
                init_player(userid)

            if event not in self.engagement_list:
                print('got event:',event, 'from:',userid)
                save_event(userid, event)
            else:
                print('got engagement:',event, 'from:',userid)
                save_engagement(userid, event)
                return userid, event

    # take an action
    def _step(self, userid_and_action):

        userid = userid_and_action[0]
        action = userid_and_action[1]
        update_action(userid, action)

        # send the response
        print('send response: ', self.Actions(action).name, 'to userid:', userid)

        reward = 0

        # receive next events
        userid, engagement = self.receive_events()

        state = query_state(userid)
        print('state:', state)

        # no last action -> new user
        if state[6] == None:
            return None, None, None, {"engagement": engagement, "userid":userid, "is_new_user":True}

        events = query_events(userid)
        print('events:', events)
        new_state = [state[2],state[3],state[4],state[5]]

        # -------------------------- deal with events ----------------------------

        # ------- ad -------
        # ad_opened event: reward + 1
        ad_open_times = len(list(filter(lambda x: x[2] == self.Events.ad_opened.name, events)))
        # ad_closed event: reward - 1
        ad_close_times = len(list(filter(lambda x: x[2] == self.Events.ad_closed.name, events)))

        reward += ad_open_times
        reward -= ad_close_times

        new_state[self.States.ad_acceptance.value] += ad_open_times
        new_state[self.States.ad_acceptance.value] -= ad_close_times
        if new_state[self.States.ad_acceptance.value] > state_threshold:
            new_state[self.States.ad_acceptance.value] = state_threshold
        if new_state[self.States.ad_acceptance.value] < 0:
            new_state[self.States.ad_acceptance.value] = 0


        # -------------------------- deal with the engagement ----------------------------

        # ------- online time -------
        if engagement == self.Engagements.online.name:
            current_time = time()
            current_params = query_online_params(userid)
            new_params = dict()
            new_params['last_online_time'] = current_time

            last_offline_time = list(filter(lambda x: x[2]==self.Events.offline.name, events))[0][4]

            new_params['time_sum'] = current_params[3] + current_time - current_params[2]
            new_params['online_time_sum'] =\
                current_params[4] + (last_offline_time - current_params[2])

            new_online_time_percent = new_params['online_time_sum']/new_params['time_sum'] * 100

            if current_params[5] != 0: # not count into reward at the first time
                reward += (new_online_time_percent - current_params[5])
            new_params['online_time_percent'] = new_online_time_percent

            update_online_params(userid, new_params)

            new_state[self.States.online_motivation.value] = int(new_online_time_percent)

        # ------- mission -------
        elif engagement == self.Engagements.mission_completed.name:
            reward += 1
            new_state[self.States.mission_skill.value] += 1
            if new_state[self.States.mission_skill.value] > state_threshold:
                new_state[self.States.mission_skill.value] = state_threshold
            

        elif engagement == self.Engagements.mission_failed.name:
            reward -= 1
            new_state[self.States.mission_skill.value] -= 1
            if new_state[self.States.mission_skill.value] < 0:
                new_state[self.States.mission_skill.value] = 0


        elif engagement == self.Engagements.transaction.name:
            reward += 2
            new_state[self.States.consumption_ability.value] += 1 # should consider about online time
            if new_state[self.States.consumption_ability.value] > state_threshold:
                new_state[self.States.consumption_ability.value] = state_threshold

        if reward != 0:
            print('reward:', reward)

        print('new state:', new_state)
        update_state(userid, new_state)

        # returns: observation (object, next_state), reward (float), done (boolean), info (dict)
        return np.array(new_state), reward, False, {"engagement": engagement, "last_state_and_action":state}


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


# -------------------
# database services
# -------------------

def save_event(userid, event):
    param = (userid, event, time(), 0)
    sql = "INSERT INTO EVENTS ('userid','event','time','status') VALUES (?,?,?,?)"
    return execute_update(sql, param)

def save_engagement(userid, engagement):
    param = (userid, engagement, time())
    sql = "INSERT INTO ENGAGEMENTS ('userid','engagement','time') VALUES (?,?,?)"
    return execute_update(sql, param)

def init_player(userid):
    result = 0

    initial_state = int(state_threshold/2)
    state_param = (userid, initial_state, initial_state, initial_state, initial_state)
    state_sql = """
    INSERT INTO STATES ('userid','online_motivation','ad_acceptance','mission_skill','consumption_ability')
    VALUES (?,?,?,?,?)
    """
    result += execute_update(state_sql, state_param)

    online_param = (userid, time())
    online_sql = "INSERT INTO ONLINE_PARAMS ('userid', 'last_online_time') VALUES (?,?)"
    result += execute_update(online_sql, online_param)

    print("init_player:", userid)

    return result

def query_state(userid):
    param = (userid, )
    sql = "SELECT * FROM STATES WHERE userid = ?"
    r = execute_query(sql, param)
    if not r:
        return r
    return r[0]

def query_events(userid):
    param = (userid, )
    sql = "SELECT * FROM EVENTS WHERE userid = ? AND status = 0"
    r = execute_query(sql, param)

    # TODO should update based on the event id list
    sql2 = "UPDATE EVENTS SET status = 1 WHERE userid = ?"
    execute_update(sql2, param)
    return r

def query_online_params(userid):
    param = (userid, )
    sql = "SELECT * FROM ONLINE_PARAMS WHERE userid = ?"
    r = execute_query(sql, param)
    if not r:
        return r
    return r[0]

def update_state(userid, new_state):
    param = (new_state[0],new_state[1],new_state[2],new_state[3],userid)
    sql = """
    UPDATE STATES SET online_motivation = ?, ad_acceptance = ?, 
    mission_skill = ?,  consumption_ability = ?
    WHERE userid = ?
    """
    execute_update(sql, param)

def update_action(userid, action):
    param = (action, userid)
    sql = "UPDATE STATES SET last_action = ? WHERE userid = ?"
    print('update_action:', param)
    execute_update(sql, param)

def update_online_params(userid, online_params):
    param = (online_params["last_online_time"], online_params["time_sum"], \
        online_params["online_time_sum"], online_params["online_time_percent"], userid)
    sql = """
    UPDATE ONLINE_PARAMS SET last_online_time = ?, time_sum = ?, 
    online_time_sum = ?,  online_time_percent = ?
    WHERE userid = ?
    """
    execute_update(sql, param)


# -------------------
# database operation utilities
# -------------------

def execute_query(sql, param = None):
    try:
        conn = sqlite3.connect(sqlite_db)
        if param == None:
            cu = conn.execute(sql)
        else:
            cu = conn.execute(sql, param)
        res = cu.fetchall()
        return res
    except Exception as e:
        print(e)
        return None
    finally:
        if conn is not None:
            conn.close()

def execute_update(sql, param = None):
    try:
        conn = sqlite3.connect(sqlite_db)
        if param == None:
            res = conn.execute(sql)
        else:
            if not type(param) == tuple:
                param = tuple(param)
            conn.execute(sql, param)
        conn.commit()
        return conn.total_changes
    except Exception as e:
        print(e)
        return 0
    finally:
        if conn is not None:
            conn.close()