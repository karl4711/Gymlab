import sqlite3
from time import time

sqlite_db = 'test.db'    

state_threshold = 100

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
    param = (int(action), userid)
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
