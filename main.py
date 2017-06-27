import qlearning
from manage import *
from flask import Flask
import test_env

PORT = 4711


app = Flask(__name__)

@app.route('/event/<userid>/<event>')
def event(userid, event):
    res = test_env.receive_event(userid, event)
    print('res:', res)
    return str(res)

@app.route('/engagement/<userid>/<engagement>')
def engagement(userid, engagement):
    res = test_env.receive_engagement(userid, engagement)
    print('res:', res)
    return res

@app.route('/dump')
def dump():
	dump_q()
	return "OK"

@app.route('/clean')
def clean():
	clean_db()
	return "OK"

if __name__ == '__main__':

    if DEBUG:
        clean_db()


    app.run(port = 4711, debug = DEBUG, host = "0.0.0.0")
    