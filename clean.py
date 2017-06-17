import sqlite3

sqlite_db = 'test.db' 

def clean():
    execute_update("DELETE FROM EVENTS")
    execute_update("DELETE FROM ENGAGEMENTS")
    execute_update("DELETE FROM ONLINE_PARAMS")
    execute_update("DELETE FROM STATES")
    print("data cleaned.")


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



if __name__ == "__main__":
    clean()

