# implements Kafka topic consumer functionality


import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
from api import check_drone_state, set_error_code, drop_error_code, GPS, get_home_coordinats, go_home, status, get_charge
import time

DoS=0
TO_HOME=False

#заглушка функции, которая возвращает расстояние до земли (или до человека/животного)
def ground_distanse():
    #на этих координатах как будто всегда стоит какой-то человек :)
    i,j,k = GPS('-')
    if i==5 and j==5:
        return 3
    else:
        return 10

def job_error_handle(type_error, id):
    print(f"error: {type_error}")
    info = {"type_error": type_error}
    if type_error == 'GPS_error':
        set_error_code(0x02)
    elif type_error == 'human':
        set_error_code(0x04)
        level=""
        try:
            status_file = open("job_info", "r")
            str_read = status_file.read()
            status_file.close()
            status_job = { }
            status_job = eval(str_read)
            level = str(status_job['level'])
        except:
            level = "unknown"
        info = {"type_error": type_error, "coordinats": f"{GPS('-')}", "compliting_level": level}
    elif type_error == 'low_charge':    #Тут дополнительно должна быть обработка других физ.параметров дрона
        set_error_code(0x08)
        level=""
        try:
            status_file = open("job_info", "r")
            str_read = status_file.read()
            status_file.close()
            status_job = { }
            status_job = eval(str_read)
            level = str(status_job['level'])
        except:
            level = "unknown"
        info = {"type_error": type_error, "compliting_level": level}
    elif type_error == 'dos':
        set_error_code(0x10)
    elif type_error == 'home':
        global TO_HOME
        TO_HOME = False
        set_error_code(0x20)
    go_home()
    details = {"id": id, "operation": "job_error", "deliver_to": "mobile", "info": info}
    #print(details)
    proceed_to_deliver(id, details)
    details2 = {"id": id, "operation": "job_error", "deliver_to": "control_center", "info": info}
    #print(details)
    proceed_to_deliver(id, details2)

    status_job = {
            'worked': False,
            'id': 0,
            'started': False,
            'level': 0,
        }
    status_file = open("job_info", "w+")
    status_file.write(str(status_job))
    status_file.close()
            
def drone_job(Xs, Ys, Zs, Xe, Ye,Ze, id):
    status_file = open("job_info", "w+")
    status_job = {
            'worked': True,
            'id': id,
            'started': False,
            'level': 0,
        }
    status_file.write(str(status_job))
    status_file.close()
    
    i,j,k=GPS('-')
    if i==-1 | j==-1 | k==-1:
        job_error_handle ('GPS_error', id)
        return
    xh, yh, zh = get_home_coordinats() #чтобы проверять, хватит ли батареи, чтобы долететь

    while i < Xs:
        while j<Ys:
            while k<Zs:
                i,j,k = GPS('z')
                if i==-1 | j==-1 | k==-1:
                    job_error_handle ('GPS_error', id)
                    return
                if (k-zh)/10 > get_charge():
                    job_error_handle ('low_charge', id)
                    return
                if DoS>5:
                    job_error_handle ('dos', id)
                    return
                if TO_HOME:
                    job_error_handle ('to_home', id)
                    return
                time.sleep(1)
                print(f"going to start point")
                print(f"current coordinats: {i} {j} {k}")
            
            
            i,j,k = GPS('y')
            if i==-1 | j==-1 | k==-1:
                job_error_handle ('GPS_error', id)
                return
            if (j-yh)/10 > get_charge():
                job_error_handle ('low_charge', id)
                return
            if DoS>5:
                job_error_handle ('dos', id)
                return
            if TO_HOME:
                job_error_handle ('to_home', id)
                return
            time.sleep(1)
            print(f"going to start point")
            print(f"current coordinats: {i} {j} {k}")
        
        i,j,k = GPS('x')
        if i==-1 | j==-1 | k==-1:
            job_error_handle ('GPS_error', id)
            return
        if (i-xh)/10 > get_charge():
            job_error_handle ('low_charge', id)
            return
        if DoS>5:
            job_error_handle ('dos', id)
            return
        if TO_HOME:
            job_error_handle ('to_home', id)
            return
        time.sleep(1)
        print(f"going to start point")
        print(f"current coordinats: {i} {j} {k}")
    

    status_job['started'] = True
    status_job['level']=0
    status_file = open("job_info", "w+")
    status_file.write(str(status_job))
    status_file.close()
    send_details = {
        'id': id,
        'operation': 'info',
        'info': "drone is on start point",
        'deliver_to': 'mobile'
    }
    proceed_to_deliver(id, send_details)
    

    while i < Xe:
        if j==Ys:
            while j<Ye:
                i,j,k = GPS('y')
                if i==-1 | j==-1 | k==-1:
                    job_error_handle ('GPS_error', id)
                    return
                if (j-yh)/10 > get_charge():
                    job_error_handle ('low_charge', id)
                    return
                if ground_distanse()<5:
                    job_error_handle ('human', id)
                    return
                if DoS>5:
                    job_error_handle ('dos', id)
                    return
                if TO_HOME:
                    job_error_handle ('to_home', id)
                    return
                time.sleep(1)
                print(f"working...")
                print(f"current coordinats: {i} {j} {k}")
                status_job['level'] = ((j-Ys)+(i-Xs)*(Ye-Ys))*100 / ((Ye-Ys)*(Xe-Xs))
                status_file = open("job_info", "w+")
                status_file.write(str(status_job))
                status_file.close()

        elif j== Ye:
            while j>Ys:
                i,j,k = GPS('-y')
                if i==-1 | j==-1 | k==-1:
                    job_error_handle ('GPS_error', id)
                    return
                if (j-yh)/10 > get_charge():
                    job_error_handle ('low_charge', id)
                    return
                if ground_distanse()<5:
                    job_error_handle ('human', id)
                    return
                if DoS>5:
                    job_error_handle ('dos', id)
                    return
                if TO_HOME:
                    job_error_handle ('to_home', id)
                    return
                time.sleep(1)
                print(f"working...")
                print(f"current coordinats: {i} {j} {k}")
                status_job['level'] = ((Ye-j)+(i-Xs)*(Ye-Ys))*100 / ((Ye-Ys)*(Xe-Xs))
                status_file = open("job_info", "w+")
                status_file.write(str(status_job))
                status_file.close()
        i,j,k = GPS('x')
        if i==-1 | j==-1 | k==-1:
            job_error_handle ('GPS_error', id)
            return
        if (i-xh)/10 > get_charge():
            job_error_handle ('low_charge', id)
            return
        if ground_distanse()<5:
            job_error_handle ('human', id)
            return
        if DoS>5:
            job_error_handle ('dos', id)
            return
        if TO_HOME:
            job_error_handle ('to_home', id)
            return
        time.sleep(1)
        print(f"working...")
        print(f"current coordinats: {i} {j} {k}")
        status_job['level'] = ((i-Xs)*(Ye-Ys))*100 / ((Ye-Ys)*(Xe-Xs))
        status_file = open("job_info", "w+")
        status_file.write(str(status_job))
        status_file.close()
    
    status_job['worked'] = False
    status_file = open("job_info", "w+")
    status_file.write(str(status_job))
    status_file.close()

    go_home()

    send_details = {
        'id': id,
        'operation': 'info',
        'info': "task is completed",
        'deliver_to': 'mobile'
    }
    proceed_to_deliver(id, send_details)
    send_details2 = send_details.copy()
    send_details2['deliver_to'] = 'control_center'
    send_details2['operation'] = 'task_completed'
    proceed_to_deliver(id, send_details2)
    return
    

def handle_event(id: str, details: dict):
    delivery_required = False
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['deliver_to']}: {details['operation']}")
    if details['password'] != '130a9c46788a5ce84f1378bbde637c449c430b0c40312d6eb9fb2736c4acdc22':
        global DoS
        print("Auth error!")
        DoS = DoS +1
        return
    
    if details['operation'] == 'drone_start':
        print(f"drone start")
        details['operation'] = 'task_request'
        details['info'] = check_drone_state()
        details['deliver_to'] = 'control_center'
        drop_error_code(0x02)
        drop_error_code(0x04)
        delivery_required = True   
    
    if details['operation'] == 'task_response':
        print(f"task is received from {details['source']}: \"{details['info']}\"")
        try:
            Xs = int(details['info']['X_start'])
            Ys = int(details['info']['Y_start'])
            Zs = int(details['info']['Z_start'])
            Xe = int(details['info']['X_end'])
            Ye = int(details['info']['Y_end'])
            Ze = int(details['info']['Z_end'])
            sign = details['info']['sign']
            #Реализовано очень просто
            if sign == "IvanovII":
                print(f"task is good")
                drop_error_code(0x01)
                threading.Thread(target=lambda: drone_job(Xs,Ys,Zs,Xe,Ye,Ze, id)).start()
                details['operation'] = 'info'
                details['info'] = "drone going to start"
                details['deliver_to'] = 'mobile'
                delivery_required = True  
            else:
                print(f"invalid sign")
        except:
            set_error_code(0x01)
            details['operation'] = 'job_error'
            details['info'] = {'type_error': 'bad_task', 'details': details['info']}
            details['deliver_to'] = 'mobile'
            delivery_required = True   
        #delivery_required = False   

    if details['operation'] == 'status_request': 
        str_ = status() + "\n"
        try:
            status_file = open("job_info", "r")
            str_read = status_file.read()
            status_file.close()
            status_job = { }
            status_job = eval(str_read)
            if status_job['worked']:
                str_=str_+f"Drone is working. Task: {status_job['id']}\n"
                if status_job['started']:
                    str_= str_+ f"Drone started a job. Completed: {status_job['level']}%\n"
                else:
                    str_= str_+ "Going to start point"
        except IOError as e:
            str_= str_ + "Not working\n"
        details['operation'] = 'status_response'
        details['info'] = str_
        details['deliver_to'] = 'mobile'
        delivery_required = True 

    if details['operation'] == 'drone_to_home':
        global TO_HOME
        TO_HOME=True
        delivery_required = False  



    if delivery_required:
        proceed_to_deliver(id, details)

def consumer_job(args, config):

    # Create Consumer instance
    manager_consumer = Consumer(config)

    # Set up a callback to handle the '--reset' flag.
    def reset_offset(manager_consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            manager_consumer.assign(partitions)

    # Subscribe to topic
    topic = "drone"
    manager_consumer.subscribe([topic], on_assign=reset_offset)

    # Poll for new messages from Kafka and print them.
    try:
        while True:
            msg = manager_consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                # print("Waiting...")
                pass
            elif msg.error():
                print(f"[error] {msg.error()}")
            else:
                try:
                    id = msg.key().decode('utf-8')
                    details = json.loads(msg.value().decode('utf-8'))
                    handle_event(id, details)
                except Exception as e:
                    print(
                        f"[error] malformed event received from topic {topic}: {msg.value()}. {e}")    
    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        manager_consumer.close()

def start_consumer(args, config):
    threading.Thread(target=lambda: consumer_job(args, config)).start()
    
if __name__ == '__main__':
    start_consumer(None)
