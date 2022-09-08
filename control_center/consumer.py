# implements Kafka topic consumer functionality


import threading
import multiprocessing
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver
from uuid import uuid4

incident_log = []
_task_queue: multiprocessing.Queue = None

def get_incident_list():
    global incident_log
    return incident_log

#заглушка функции, которая проверяет задание на безопасность
def check_task(details):
    return True

#Функция получает из очереди задание и проверяет его. 
# Если возвращается пустая строка, то хорошего задания нет
def get_task():
    while _task_queue.qsize()>0:
        task_details = _task_queue.get()
        if check_task(task_details):
            return task_details
        else:
            print(f"bad task was deleted: "+ task_details) 
    return "" 

def handle_event(id: str, details: dict):
    delivery_required = False
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['deliver_to']}: {details['operation']}")
    if details['operation'] == 'task_request':
        print(f"event: task request")
        details['operation'] = 'task_info'
        details['info'] = get_task()
        details['deliver_to'] = 'mobile'
        #отправили сначала мп, позже отправим дрону
        proceed_to_deliver(id, details)
        details2 = details.copy()
        details2['operation'] = 'task_response'
        details2['deliver_to'] = 'drone'
        proceed_to_deliver(id, details2)
        delivery_required = False

    if details['operation'] == 'job_error':
        print(f"get error info: {details['info']}")
        global incident_log
        incident_log.append(details)
        delivery_required = False

    if details['operation'] == 'task_completed':
        print(f"Task {details['id']} is completed")
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
    topic = "control_center"
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

def start_consumer(args, config, task_queue):
    global _task_queue 
    _task_queue = task_queue
    threading.Thread(target=lambda: consumer_job(args, config)).start()
    
if __name__ == '__main__':
    start_consumer(None)
