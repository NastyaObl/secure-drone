id_list = []
def check_operation(id, details):
    authorized = False
    # print(f"[debug] checking policies for event {id}, details: {details}")
    print(f"[info] checking policies for event {id},"\
          f" {details['source']}->{details['deliver_to']}: {details['operation']}")
    src = details['source']
    dst = details['deliver_to']
    operation = details['operation']
    if  src == 'downloader' and dst == 'manager' \
        and operation == 'download_done':
        authorized = True    
    if src == 'manager' and dst == 'downloader' \
        and operation == 'download_file':
        authorized = True    
    if src == 'manager' and dst == 'storage' \
        and operation == 'commit_blob':
        authorized = True    
    if src == 'manager' and dst == 'verifier' \
        and operation == 'verification_requested':
        authorized = True    
    if src == 'verifier' and dst == 'manager' \
        and operation == 'handle_verification_result':
        authorized = True    
    if src == 'manager' and dst == 'updater' \
        and operation == 'proceed_with_update' \
        and details['verified'] is True:
        authorized = True    
    if src == 'storage' and dst == 'manager' \
        and operation == 'blob_committed':
        authorized = True    
    if src == 'verifier' and dst == 'storage' \
        and operation == 'get_blob':
        authorized = True
    if src == 'storage' and dst == 'verifier' \
        and operation == 'blob_content':
        authorized = True    
    if src == 'updater' and dst == 'storage' \
        and operation == 'get_blob':
        authorized = True
    if src == 'storage' and dst == 'updater' \
        and operation == 'blob_content':
        authorized = True 

    if src == 'drone' and dst == 'mobile' \
        and operation == 'info':
        authorized = True  
    if src == 'mobile' and dst == 'drone' \
        and operation == 'drone_start':
        authorized = True   
    if src == 'drone' and dst == 'control_center' \
        and operation == 'task_request':
        authorized = True   
    if src == 'control_center' and dst == 'drone' \
        and operation == 'task_response':
        authorized = True   
        id_list.append(details['id'])       #делаем как бы statefull соединение
    if src == 'control_center' and dst == 'mobile' \
        and operation == 'task_info':
        authorized = True   
    if src == 'drone' and dst == 'mobile' \
        and operation == 'job_error':
        authorized = True  
    if src == 'drone' and dst == 'control_center' \
        and operation == 'job_error' and details['id'] in id_list:
        authorized = True 
    if src == 'mobile' and dst == 'drone' \
        and operation == 'status_request':
        authorized = True   
    if src == 'drone' and dst == 'mobile' \
        and operation == 'status_response':
        authorized = True   
    if src == 'mobile' and dst == 'drone' \
        and operation == 'drone_to_home':
        authorized = True 
    if src == 'drone' and dst == 'control_center' \
        and operation == 'task_completed':
        authorized = True 
        
    
    return authorized