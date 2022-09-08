import multiprocessing
from flask import Flask, request, jsonify
import threading
from consumer import get_incident_list 

host_name = "0.0.0.0"
port = 5050

app = Flask(__name__)             # create an app instance

APP_VERSION = "1.0.2"

_requests_queue: multiprocessing.Queue = None
_task_queue: multiprocessing.Queue = None

@app.route("/add_task", methods=['POST'])
def add_task():
    content = request.json
    auth = request.headers['auth']
    if auth != 'very-secure-token':
        return "unauthorized", 401

    try:
        task_details = {
            "X_start": content['X_start'],
            "Y_start": content['Y_start'],
            "Z_start": content['Z_start'],
            "X_end": content['X_end'],
            "Y_end": content['Y_end'],
            "Z_end": content['Z_end'],
            "sign": content['sign']
            }
        _task_queue.put(task_details)
        print(f"new task: {task_details}")
    except:
        error_message = f"malformed request {request.data}"
        print(error_message)
        return error_message, 400
    return jsonify({"number of task": _task_queue.qsize()})

@app.route("/incident_info")
def incident_info():
    l = get_incident_list()
    if len(l)>0:
        return f"{l}"
    else:
        return "log is empty"

def start_rest(requests_queue, task_queue):
    global _requests_queue 
    global _task_queue 
    _requests_queue = requests_queue
    _task_queue = task_queue
    threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=True, use_reloader=False)).start()

if __name__ == "__main__":        # on running python app.py
    start_rest()