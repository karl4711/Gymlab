import logging
import numpy as np
from time import time
from pdb import set_trace
import qlearning
from services import *
from enums import *

logger = logging.getLogger(__name__)

state_threshold = 100    

# see Actions
action_space = [0,1,2,3,4]

# online_motivation(0-99), ad_acceptance(0-99), mission_skill(0-99), consumption_ability(0-99)
# x = np.array(np.arange(pow(state_threshold,4)))
# observation_space = np.reshape(x,(state_threshold,state_threshold,state_threshold,state_threshold))

# TODO we only learn the first two dimensions for test (since Q is too large)
x = np.array(np.arange(pow(state_threshold,2)))
observation_space = np.reshape(x,(state_threshold,state_threshold))

engagement_list = list(map(lambda x: x.name, Engagements))

def receive_event(userid, event):

    print('got event:',event, 'from:',userid)
    return save_event(userid, event)

    # TODO may save userids in memory 
    if not query_state(userid):
        print("user not exist, initialise here.", userid)
        init_player(userid)


def receive_engagement(userid, engagement):

    print('got engagement:',engagement, 'from:',userid)
    save_engagement(userid, engagement)

    # first engagement(online), learn nothing
    if not query_state(userid):
        print("user not exist, initialise here.", userid)
        init_player(userid)
        state = query_state(userid)
        last_state = [state[2],state[3],state[4],state[5]]
        action = qlearning.step(np.array(last_state), engagement)
        update_action(userid, action)
        return Actions(action).name

    reward = 0

    state = query_state(userid)
    print('state:', state)
    last_state = [state[2],state[3],state[4],state[5]]
    last_action = state[6]

    # no last action -> new user
    is_new_user = last_action == None

    events = query_events(userid)
    print('events:', events)
    new_state = [state[2],state[3],state[4],state[5]]

    # -------------------------- deal with events ----------------------------

    # ------- ad -------
    # ad_opened event: reward + 1
    ad_open_times = len(list(filter(lambda x: x[2] == Events.ad_opened.name, events)))
    # ad_closed event: reward - 1
    ad_close_times = len(list(filter(lambda x: x[2] == Events.ad_closed.name, events)))

    reward += ad_open_times
    reward -= ad_close_times

    new_state[States.ad_acceptance.value] += ad_open_times
    new_state[States.ad_acceptance.value] -= ad_close_times
    if new_state[States.ad_acceptance.value] > state_threshold:
        new_state[States.ad_acceptance.value] = state_threshold
    if new_state[States.ad_acceptance.value] < 0:
        new_state[States.ad_acceptance.value] = 0


    # -------------------------- deal with the engagement ----------------------------

    # ------- online time -------
    if engagement == Engagements.online.name:
        current_time = time()
        current_params = query_online_params(userid)
        new_params = dict()
        new_params['last_online_time'] = current_time

        last_offline_time = list(filter(lambda x: x[2]==Events.offline.name, events))[0][4]

        new_params['time_sum'] = current_params[3] + current_time - current_params[2]
        new_params['online_time_sum'] =\
            current_params[4] + (last_offline_time - current_params[2])

        new_online_time_percent = new_params['online_time_sum']/new_params['time_sum'] * 100

        if current_params[5] != 0: # not count into reward at the first time
            reward += (new_online_time_percent - current_params[5])
        new_params['online_time_percent'] = new_online_time_percent

        update_online_params(userid, new_params)

        new_state[States.online_motivation.value] = int(new_online_time_percent)

    # TODO we do not concern about these two dimensions for test
    # # ------- mission -------
    # elif engagement == Engagements.mission_completed.name:
    #     reward += 1
    #     new_state[States.mission_skill.value] += 1
    #     if new_state[States.mission_skill.value] > state_threshold:
    #         new_state[States.mission_skill.value] = state_threshold
        

    # elif engagement == Engagements.mission_failed.name:
    #     reward -= 1
    #     new_state[States.mission_skill.value] -= 1
    #     if new_state[States.mission_skill.value] < 0:
    #         new_state[States.mission_skill.value] = 0

    # # ------- transaction -------
    # elif engagement == Engagements.transaction.name:
    #     reward += 2
    #     new_state[States.consumption_ability.value] += 1 # should consider about online time
    #     if new_state[States.consumption_ability.value] > state_threshold:
    #         new_state[States.consumption_ability.value] = state_threshold

    if reward != 0:
        print('reward:', reward)

    print('new state:', new_state)
    update_state(userid, new_state)

    action = qlearning.step(np.array(new_state), engagement)
    update_action(userid, action)

    qlearning.learn(np.array(new_state), reward, np.array(last_state), last_action, is_new_user)

    return Actions(action).name


# only some of the actions are valid according to current engagement
def get_valid_actions(engagement):
    valid_actions = []
    if engagement not in engagement_list:
        pass
    elif engagement == Engagements.online.name:
        valid_actions = [Actions.send_award.value, Actions.show_ad.value, Actions.goods_recommend.value]
    elif engagement == Engagements.level_up.name:
        valid_actions = [Actions.send_award.value]
    elif engagement == Engagements.mission_completed.name:
        valid_actions = [Actions.send_award.value, Actions.increase_difficulty.value, Actions.decrease_difficulty.value]
    elif engagement == Engagements.mission_failed.name:
        valid_actions = [Actions.decrease_difficulty.value, Actions.goods_recommend.value]
    elif engagement == Engagements.transaction.name:
        valid_actions = [Actions.send_award.value, Actions.goods_recommend.value]

    return np.array(valid_actions)

