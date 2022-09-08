import imp
import multiprocessing
from flask import Flask, request, jsonify
from uuid import uuid4
import threading
from consumer import get_status_drone
import datetime
from hashlib import sha256
import base64

host_name = "0.0.0.0"
port = 9876

app = Flask(__name__)             # create an app instance

APP_VERSION = "1.0.2"

_requests_queue: multiprocessing.Queue = None

@app.route("/drone_work", methods=['POST'])
def drone_work():
    content = request.json
    auth = request.headers['auth']
    if auth != 'very-secure-token':
        return "unauthorized", 401
    if content['PIN'] != '1234':
        return "unauthorized", 401

    req_id = uuid4().__str__()
    b64 = base64.b64decode(content['drone_password'])
    pass_hash = sha256(b64).hexdigest()

    try:
        start_details = {
            "id": req_id,
            "operation": "drone_start",
            "password": pass_hash,
            "deliver_to": "drone",
            "info": ""
            }
        _requests_queue.put(start_details)
        print(f"event: {start_details}")
    except:
        error_message = f"malformed request {request.data}"
        print(error_message)
        return error_message, 400
    return jsonify({"operation": "drone_start", "id": req_id})

@app.route("/drone_status", methods=['POST'])
def drone_status():
    
    content = request.json
    auth = request.headers['auth']
    if auth != 'very-secure-token':
        return "unauthorized", 401
    if content['PIN'] != '1234':
        return "unauthorized", 401

    req_id = uuid4().__str__()

    b64 = base64.b64decode(content['drone_password'])
    pass_hash = sha256(b64).hexdigest()
    
    try:
        details = {
            "id": req_id,
            "operation": "status_request",
            "deliver_to": "drone",
            "password": pass_hash,
            "info": ""
            }
        _requests_queue.put(details)
        print(f"status wait...")
        str_status = ""
        t1 = datetime.datetime.now()
        while len(str_status)==0:
            str_status = get_status_drone()
            t2 = datetime.datetime.now()
            td = t2-t1
            if td.total_seconds() > 10:
                return "No response"
        return str_status
    except:
        error_message = f"malformed request {request.data}"
        print(error_message)
        return error_message, 400

@app.route("/drone_to_home", methods=['POST'])
def drone_to_home():
    
    content = request.json
    auth = request.headers['auth']
    if auth != 'very-secure-token':
        return "unauthorized", 401
    if content['PIN'] != '1234':
        return "unauthorized", 401

    req_id = uuid4().__str__()

    b64 = base64.b64decode(content['drone_password'])
    pass_hash = sha256(b64).hexdigest()
    
    try:
        details = {
            "id": req_id,
            "operation": "drone_to_home",
            "deliver_to": "drone",
            "password": pass_hash,
            "info": ""
            }
        _requests_queue.put(details)
        return "home request is sent"
    except:
        error_message = f"malformed request {request.data}"
        print(error_message)
        return error_message, 400

def start_rest(requests_queue):
    global _requests_queue 
    _requests_queue = requests_queue
    threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=True, use_reloader=False)).start()

if __name__ == "__main__":        # on running python app.py
    start_rest()