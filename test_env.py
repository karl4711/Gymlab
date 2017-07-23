import logging
import numpy as np
from time import time
from pdb import set_trace
import qlearning
from services import *
from enums import *
from manage import *

# see Actions
action_space = [0,1,2,3,4]

# online_motivation(0-9), ad_acceptance(0-9), mission_skill(0-9), consumption_ability(0-9)
# x = np.array(np.arange(pow(state_threshold,4)))
# observation_space = np.reshape(x,(state_threshold,state_threshold,state_threshold,state_threshold))

# TODO we only learn the first two dimensions for test (since Q is too large)
x = np.array(np.arange(pow(state_threshold,4)))
observation_space = np.reshape(x,(state_threshold,state_threshold,state_threshold,state_threshold))

engagement_list = list(map(lambda x: x.name, Engagements))

def receive_event(userid, event, params):

    print('got event:',event, 'from:',userid)
    return save_event(userid, event, params)

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
        action = qlearning.step(last_state, engagement)
        update_action_and_reward(userid, action, 0)
        return Actions(action).name

    reward = 0

    state = query_state(userid)
    print('state:', state)
    last_state = [state[2],state[3],state[4],state[5]]
    last_action = state[6]

    # no last action -> new user
    is_new_user = last_action == None

    # query events
    events = query_events(userid)
    print('events:', events)
    new_state = [state[2],state[3],state[4],state[5]]


    # query online params
    current_online_params = query_online_params(userid)
    online_time_sum = current_online_params[4]
    last_online_time = current_online_params[2]


    # ------- ad -------
    # ad_opened event: reward + 1
    ad_open_times = len(list(filter(lambda x: x[2] == Events.ad_opened.name, events)))
    # ad_closed event: reward - 1
    ad_close_times = len(list(filter(lambda x: x[2] == Events.ad_closed.name, events)))

    reward += (ad_open_times * 2)
    reward -= ad_close_times

    if ad_open_times != 0 or ad_close_times != 0:
        current_ad_params = query_ad_params(userid)
        current_open_times = current_ad_params[2]
        current_close_times = current_ad_params[3]
        new_ad_params = dict()
        new_ad_params['ad_open_times'] = current_open_times + ad_open_times
        new_ad_params['ad_close_times'] = current_close_times + ad_close_times

        update_ad_params(userid, new_ad_params)

        new_state[States.ad_acceptance.value] = int(new_ad_params['ad_open_times'] / \
            (new_ad_params['ad_open_times'] + new_ad_params['ad_close_times']) * 10)

        if new_state[States.ad_acceptance.value] >= state_threshold:
            print('ad_acceptance of', userid, 'exceed threshold !!!')
            new_state[States.ad_acceptance.value] = state_threshold - 1

    # ------- online time -------
    if engagement == Engagements.online.name:
        current_time = time()
        
        new_params = dict()
        new_params['last_online_time'] = current_time

        last_offline_time = list(filter(lambda x: x[2]==Events.offline.name, events))[0][4]

        new_params['time_sum'] = current_online_params[3] + current_time - current_online_params[2]
        new_params['online_time_sum'] =\
            current_online_params[4] + (last_offline_time - current_online_params[2])

        new_online_time_percent = new_params['online_time_sum']/new_params['time_sum'] * 100

        if current_online_params[5] != 0: # not count into reward at the first time
            reward += (new_online_time_percent - current_online_params[5])
        new_params['online_time_percent'] = new_online_time_percent

        online_time_sum = new_params['online_time_sum']

        update_online_params(userid, new_params)

        new_state[States.online_motivation.value] = int(new_online_time_percent / 10)


    # ------- transaction (update here since it depends on the online time params) -------
    current_tr_params = query_transaction_params(userid)
    tr_amount = current_tr_params[2]
    
    total_consumption = sum(int(e[3]) for e in list(filter(lambda x: x[2] == Events.transaction.name, events)))

    if total_consumption > 0:
        
        tr_amount += total_consumption
        update_transaction_params(userid, tr_amount)

        reward += total_consumption # TODO temp transaction reward

    if online_time_sum == 0: # only online for once until now
        online_time_sum = time() - last_online_time
    new_state[States.consumption_ability.value] = int(tr_amount / online_time_sum) # TODO temp transaction state
    print('update consumption_ability:', userid, 'spend',tr_amount,'in',online_time_sum)

    if new_state[States.consumption_ability.value] >= state_threshold:
        print('consumption_ability of', userid, 'exceed threshold !!!')
        new_state[States.consumption_ability.value] = state_threshold - 1


    # ------- mission ------- 
    if engagement in [Engagements.mission_completed.name, Engagements.mission_failed.name]:
        
        is_completed = (engagement == Engagements.mission_completed.name)

        reward += (is_completed and 1 or -1)

        current_mission_params = query_mission_params(userid)
        current_completed_times = current_mission_params[2]
        current_failed_times = current_mission_params[3]
        new_mission_params = dict()
        new_mission_params['mission_completed_times'] = current_completed_times
        new_mission_params['mission_failed_times'] = current_failed_times
        if is_completed:
            new_mission_params['mission_completed_times'] += 1
        else:
            new_mission_params['mission_failed_times'] += 1

        update_mission_params(userid, new_mission_params)

        new_state[States.mission_skill.value] = int(new_mission_params['mission_completed_times'] / \
            (new_mission_params['mission_completed_times'] + new_mission_params['mission_failed_times']) * 10)

        if new_state[States.mission_skill.value] >= state_threshold:
            print('mission_skill of', userid, 'exceed threshold !!!')
            new_state[States.mission_skill.value] = state_threshold - 1

    
    if reward != 0:
        print('reward:', reward)

    print('new state:', new_state)
    update_state(userid, new_state)

    action = qlearning.step(new_state, engagement)
    update_action_and_reward(userid, action, reward)

    qlearning.learn(new_state, reward, last_state, last_action, is_new_user)

    return Actions(action).name


# only some of the actions are valid according to current engagement
def get_valid_actions(engagement):

    valid_actions = []
    if engagement not in engagement_list:
        pass
    elif engagement == Engagements.online.name:
        valid_actions = [Actions.send_award.value, Actions.show_ad.value, Actions.goods_recommend.value]
    elif engagement == Engagements.level_up.name:
        valid_actions = [Actions.send_award.value, Actions.show_ad.value, Actions.goods_recommend.value]
    elif engagement == Engagements.mission_completed.name:
        valid_actions = [Actions.send_award.value, Actions.increase_difficulty.value, \
            Actions.decrease_difficulty.value, Actions.show_ad.value, Actions.goods_recommend.value]
    elif engagement == Engagements.mission_failed.name:
        valid_actions = [Actions.decrease_difficulty.value, Actions.goods_recommend.value, Actions.show_ad.value]
    elif engagement == Engagements.transaction.name:
        valid_actions = [Actions.send_award.value, Actions.goods_recommend.value, Actions.show_ad.value]

    return np.array(valid_actions)

