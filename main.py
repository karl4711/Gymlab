import qlearning
from manage import *
from flask import Flask, request
import test_env
import logging

PORT = 4711


app = Flask(__name__)

@app.route('/event/<userid>/<event>')
def event(userid, event):
    params = request.args.get('params')
    if not params:
        params = 0

    res = test_env.receive_event(userid, event, params)
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
    