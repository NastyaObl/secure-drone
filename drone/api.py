import multiprocessing
from flask import Flask, request, jsonify
from uuid import uuid4
import threading

host_name = "0.0.0.0"
port = 1234

app = Flask(__name__)             # create an app instance

#APP_VERSION = "1.0.2"

_requests_queue: multiprocessing.Queue = None

#Переменные, описывающие состояние дрона
TURNED_ON = False
CHARGE = 100
LEVEL_OF_BLEND = 100
STATE_OF_DEVICE = True
ERROR_CODE = 0

#чит переменная для проверки работы при ошибках навигации
BAD_GPS = False

#Переменные для сохранения домашних координат GPS
Hx=0
Hy=0
Hz=0

#Переменные для сохранения текущих координат GPS
Cx=0
Cy=0
Cz=0

def set_error_code(new_code):
    global ERROR_CODE
    ERROR_CODE = ERROR_CODE | new_code
def drop_error_code(new_code):
    global ERROR_CODE
    ERROR_CODE = ERROR_CODE & (~new_code)
def get_home_coordinats():
    global Hx, Hy, Hz
    return Hx, Hy, Hz
def go_home():
    global Cx, Cy, Cz, Hx, Hy, Hz
    Cx = Hx
    Cy = Hy
    Cz = Hz
def get_charge():
    global CHARGE
    return CHARGE

def check_drone_state():
    if TURNED_ON == True :
        if CHARGE>15: 
            if LEVEL_OF_BLEND >15:
                if STATE_OF_DEVICE == True:
                    return f"Ready to start"
                else:
                    return f"Device error"
            else:
                return f"Level of blend is low"
        else:
            return f"Level of charge is low"
    else: return f"Drone is turned off"

#Функция, которая должна возвращать текущие координаты GPS 
# Для простоты считается, что координаты могут быть только положительные 
# Если функция возвращает отрицательное значение, то это индикатор ошибки модуля GPS 
# Для простоты и имитации движения на вход подается направление движения 
# Если вместо направления ввести "-", то функция вернеть текущие координаты
def GPS (v):
    global Cx, Cy, Cz
    global BAD_GPS
    if BAD_GPS:
        BAD_GPS = False
        return -1, -1, -1
    if v == '-':    
        return Cx,Cy,Cz
    elif v == 'x':
        Cx= Cx+1
    elif v == 'y':
        Cy = Cy+1
    elif v == '-y':
        Cy = Cy -1
    elif v=='z':
        Cz = Cz+1
    else:
        return -1, -1, -1
    return Cx,Cy,Cz

@app.route("/turn_on",  methods=['POST'])                   
def turn_on():
    global TURNED_ON 
    global CHARGE
    global LEVEL_OF_BLEND
    global STATE_OF_DEVICE
    global Hx, Hy, Hz
    TURNED_ON = True
    Hx, Hy, Hz = GPS('-')        

    content = request.json
    if 'charge' in content:
        CHARGE = int(content['charge'])
    if 'level_of_blend' in content:
        LEVEL_OF_BLEND = int(content['level_of_blend'])
    if 'state_of_device' in content:
        STATE_OF_DEVICE = bool(content['state_of_device'])
    
    req_id = uuid4().__str__()
    try:
        state_details = {
            "id": req_id,
            "operation": "info",
            "deliver_to": "mobile",
            "info": "Drone is turned on.\nCharge: " + str(CHARGE) +"%\nLevel of blend:  " + str(LEVEL_OF_BLEND) + "%\nState of devices: " + str(STATE_OF_DEVICE) + ".\n" + check_drone_state()
            }
        _requests_queue.put(state_details)
        print(f"event: {state_details}")
    except:
        error_message = f"malformed request {request.data}"
        print(error_message)
        return error_message, 400
    return f"Drone is turned on.\nCharge: {CHARGE}%\nLevel of blend: {LEVEL_OF_BLEND}%\nState of devices: {STATE_OF_DEVICE}.\n" + check_drone_state()   


@app.route("/status")                   
def status():        
    if TURNED_ON:  
        str_ =  f"Charge: {CHARGE}%\nLevel of blend: {LEVEL_OF_BLEND}%\nState of devices: {STATE_OF_DEVICE}.\n"            
        str_ = str_+ f"Current coordinats: {GPS('-')} \n"
        if ERROR_CODE &0x01:
            str_=str_+"Error connection with Control Center (bad task)\n"
        if ERROR_CODE &0x02:
            str_=str_+"GPS error\n"
        if ERROR_CODE &0x04:
            str_=str_+"Last task is not completed because of human/animal/building\n"
        if ERROR_CODE &0x08:
            str_=str_+"Last task is not completed because of low charge level\n"
        if ERROR_CODE &0x10:
            str_=str_+"Last task is not completed because of DoS-attacks\n"
        if ERROR_CODE &0x20:
            str_=str_+"Last task was forced to end\n"
    else:
        str_ = "Drone is turned off"    
    return str_

@app.route("/bad_GPS")                   
def bad_GPS():        
    global BAD_GPS
    BAD_GPS=True
    return "ok"
        
    

def start_rest(requests_queue):
    global _requests_queue 
    _requests_queue = requests_queue
    Cx=Cy=Cz=0
    threading.Thread(target=lambda: app.run(host=host_name, port=port, debug=True, use_reloader=False)).start()

if __name__ == "__main__":        # on running python app.py
    start_rest()