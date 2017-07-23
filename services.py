import sqlite3
from time import time
from manage import *


def save_event(userid, event, params):
    param = (userid, event, params, time(), 0)
    sql = "INSERT INTO EVENTS ('userid','event', 'params', 'time','status') VALUES (?,?,?,?,?)"
    return execute_update(sql, param)

def save_engagement(userid, engagement):
    param = (userid, engagement, time())
    sql = "INSERT INTO ENGAGEMENTS ('userid','engagement','time') VALUES (?,?,?)"
    return execute_update(sql, param)

def init_player(userid):
    result = 0

    initial_state = int(state_threshold/2)
    state_param = (userid, initial_state, initial_state, initial_state, 0)
    state_sql = """
    INSERT INTO STATES ('userid','online_motivation','ad_acceptance','mission_skill','consumption_ability','create_time')
    VALUES (?,?,?,?,?,datetime('now'))
    """
    result += execute_update(state_sql, state_param)

    online_param = (userid, time())
    online_sql = """
    INSERT INTO ONLINE_PARAMS ('userid', 'last_online_time') VALUES (?,?)
    """
    result += execute_update(online_sql, online_param)

    ad_param = (userid, 0, 0)
    ad_sql = """
    INSERT INTO AD_PARAMS ('userid', 'ad_open_times', 'ad_close_times') VALUES (?,?,?)
    """
    result += execute_update(ad_sql, ad_param)

    mission_param = (userid, 0, 0)
    mission_sql = """
    INSERT INTO MISSION_PARAMS ('userid', 'mission_completed_times', 'mission_failed_times') VALUES (?,?,?)
    """
    result += execute_update(mission_sql, mission_param)

    tr_param = (userid, 0)
    tr_sql = """
    INSERT INTO TRANSACTION_PARAMS ('userid', 'amount') VALUES (?,?)
    """
    result += execute_update(tr_sql, tr_param)

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

def query_ad_params(userid):
    param = (userid, )
    sql = "SELECT * FROM AD_PARAMS WHERE userid = ?"
    r = execute_query(sql, param)
    if not r:
        return r
    return r[0]

def query_mission_params(userid):
    param = (userid, )
    sql = "SELECT * FROM MISSION_PARAMS WHERE userid = ?"
    r = execute_query(sql, param)
    if not r:
        return r
    return r[0]


def query_transaction_params(userid):
    param = (userid, )
    sql = "SELECT * FROM TRANSACTION_PARAMS WHERE userid = ?"
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

def update_action_and_reward(userid, action, reward):
    param = (int(action), int(reward), userid)
    sql = "UPDATE STATES SET last_action = ?, total_reward = total_reward + ? WHERE userid = ?"
    print('update user', userid, 'action:', action, 'reward:', reward)
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


def update_ad_params(userid, ad_params):
    param = (ad_params["ad_open_times"], ad_params["ad_close_times"], userid)
    sql = 'UPDATE AD_PARAMS SET ad_open_times = ?, ad_close_times = ? WHERE userid = ?'
    execute_update(sql, param)


def update_mission_params(userid, mission_params):
    param = (mission_params["mission_completed_times"], mission_params["mission_failed_times"], userid)
    sql = 'UPDATE MISSION_PARAMS SET mission_completed_times = ?, mission_failed_times = ? WHERE userid = ?'
    execute_update(sql, param)


def update_transaction_params(userid, amount):
    param = (amount, userid)
    sql = 'UPDATE TRANSACTION_PARAMS SET amount = ? WHERE userid = ?'
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
