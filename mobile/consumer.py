# implements Kafka topic consumer functionality


import threading
from confluent_kafka import Consumer, OFFSET_BEGINNING
import json
from producer import proceed_to_deliver

STATUS_DRONE = ""
def get_status_drone():
    global STATUS_DRONE
    str_ = "" + STATUS_DRONE
    STATUS_DRONE = ""
    return str_

def handle_event(id: str, details: dict):
    delivery_required = False
    # print(f"[debug] handling event {id}, {details}")
    print(f"[info] handling event {id}, {details['source']}->{details['deliver_to']}: {details['operation']}")
    if details['operation'] == 'info':
        print(f"get info from {details['source']}: \"{details['info']}\"")
        delivery_required = False   
    
    if details['operation'] == 'task_info':
        print(f"get task_info from {details['source']}: \"{details['info']}\"")
        delivery_required = False   
    
    if details['operation'] == 'job_error':
        
        print(f"get error info from {details['source']}: \"{details['info']}\"")
        delivery_required = False   
    
    if details['operation'] == 'status_response':
        print("Status is received")
        global STATUS_DRONE
        STATUS_DRONE = details['info']
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
    topic = "mobile"
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
