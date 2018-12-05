import sys
import argparse
import os
import time
import pprint
from socket_utils import *
try:
    import awscam
except ImportError:
    print("WARNING: AWSCAM is not available in this device")
from multiprocessing.connection import Listener, Client
import socket
from threading import Thread

global local_address_m
local_address_m = ('localhost', 6000)

# Local Test Dir
model_dir = "/opt/awscam/artifacts"
remote_dir = "/home/aws_cam/Desktop/remote_model"

'''
Model_Dict (key, value):
key = model's nickname for switch model
value = (model_path, awscam.Model)
'''
class Model_Dict(object):

    def __init__(self):
        self._dict = dict()
        
    def get_all_dict(self):
        return self._dict

    def len(self):
        return len(self._dict)

    def get_model_path(self):
        return self._dict[key][0]

    def get_model(self, key):
        return self._dict[key][1]

    def set_dict(self, key, value):
        self._dict[key] = [value, awscam.Model(value, {'GPU': 1})]

model_dict = Model_Dict()


'''
Starting Service with parsing all the local model path you
want to deploy into GPU
'''
def _get_parser():
    parser = argparse.ArgumentParser(description="Start Model Management- A preload model pool for user model switch")

    parser.add_argument(
        "--models_path", "-mps",
        nargs="*",
        required=True,
        help="Declare all the models path you want to preload")

    return parser


'''
Preload declared model into GPU, and update metadata with
append "model_dict[nickname] = (model_path, model)"
'''
def preload_models(models_path):
    models_num = len(models_path)

    for i in xrange(models_num):
        try:
            start_time = time.time()
            model_name = models_path[i].rsplit('/', 1)[-1].split('.')[0]
            model_dict.set_dict(model_name, models_path[i])
            print("Intel Pre-trained Object Detection Model {0} Loaded. Time Cost: {1}".format(
                model_name, time.time() - start_time))

        except Exception as ex:
            print(ex)


'''
Listener used for model migration to remote device in 
distributed model management system.
'''
def remote_listener():
    server = create_server_socket(0)

    def handle_client_connection(conn):
        name = conn.recv(1024)
        print("Receive request for {}".format(name))
        
        #TODO: get model_path from metadata
        model_path = os.path.join(model_dir, name + ".xml")  
        param_path = os.path.join(model_dir, name + ".bin")     
        #TODO: check send model
        send_file(conn, model_path)
        send_file(conn, param_path)
        #TODO: update metadata

        conn.send('ACK')
        conn.close()

    while True:
        print("[MODEL] Remote Listener start listening")
        conn, address = server.accept()
        print("Accept connection from {}:{}".format(address[0], address[1]))
        client_handler = Thread(target = handle_client_connection, args = (conn,), name = "remoteListenerWorker")
        client_handler.start()


'''
Fetch remote model through local router
'''
def fetch_remote_model(nickname):
    #TODO: address = ?
    ip = 'localhost'
    conn = create_client_socket(ip, 0)
    conn.send(nickname)

    #TODO: check file recv
    model_path = os.path.join(remote_dir, nickname + ".xml")
    param_path = os.path.join(remote_dir, nickname + ".bin")
    recv_file(conn, model_path)
    recv_file(conn, param_path)

    response = conn.recv(1024)
    if response == "ACK":
        print("Receive ACK from remote")
        conn.close()

    preload_models([model_path])

    #TODO: broadcast metadata update and self metadata update


'''
Local listener, receive message(data) from Application 
Layer and send back the inference results.
'''
def local_listener():
    listener = Listener(local_address_m, authkey="localModel")
    while True:
        conn = listener.accept()
        print("[MODEL] connection accepted from", listener.last_accepted)        
        msg = conn.recv()
        # print(msg)

        assert isinstance(msg, list) and len(msg) == 3
        task = msg[0]
        frame = msg[1]
        nickname = msg[2]
        if nickname not in model_dict.get_all_dict().keys():
            '''
            t_tmp = Thread(target=fetch_remote_model, args=(nickname,), name="tmpDeployRemoteModel")
            t_tmp.start()
            # Use Default Model
            print("Model not found at local, fetch from remote, switch to default model")
            nickname = 'deploy_ssd_mobilenet_512'
            '''
            fetch_remote_model(nickname)

        ans = model_dict.get_model(nickname).parseResult(task, 
                                    model_dict.get_model(nickname).doInference(frame))
        conn.send(ans)
        conn.close()

    listener.close()


'''
Service Main Function
'''
def main():
    parser = _get_parser()
    args = parser.parse_args()
    models_path = args.models_path
    
    # Start preload default model
    preload_models(models_path)

    # Start a thread hearing from local application layer
    t_local = Thread(target=local_listener, name="localListener")
    t_local.start()

    # Start a thread hearing from remote devices
    t_remote = Thread(target=remote_listener, name="remoteListener")
    t_remote.start()

    # Set service timeout default 10 * 60
    timeout = 10 * 60
    time.sleep(timeout)
    t_local.join()
    t_remote.join()


if __name__=="__main__":
    main()