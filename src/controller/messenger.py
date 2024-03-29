import sys
import os
from src.socket_utils import *
from threading import Thread
import time

def send_message(*args):
    # TODO: find ip address from metadata
    conn = create_client_socket(args[0], 2)

    '''
    TODO: stop or (stop + pause) ?
    Message Format
    run    | idx | task | model | video
    switch | idx | task | model | video
    stop   | idx
    '''
    # TODO: what instruction to send
    ins = ""
    for s in args[1:]:
        ins = ins + s + "|"
    print(ins[:-1])
    conn.send(ins[:-1])

    res = conn.recv(1024)
    if res == "ACK":
        print("[CRTL] Receive ACK from remote")
        conn.close()


def trigger():
    server = create_server_socket(3)

    def handle_client_connection(conn):
        # msg format = |...ip...|..func..|..res...|
        msg = conn.recv(1024)
        ip, func, res = msg.split("|")
        print("[CRTL] Get Results {0:20} from [ip:{1}]. Start {2} ...".format(res, ip, func))

        # TODO: deal with instruction
        '''
        TODO: controller logic (spotlight search)...
        should return the results for which devices begin to run and which stop
        '''
        # DUMMY LOGIC
        if ip == "10.150.92.158" and func == "ssd":
            send_message("10.150.92.158", "stop", "foo")
            time.sleep(5)
            send_message("10.150.243.250", "run", "bar", "ssd", "deploy_ssd_mobilenet_512", "AWSCAM")


        conn.send("ACK")
        conn.close()

    while True:
        print("[CRTL] Controller start listening")
        conn, address = server.accept()
        print("[CRTL] Accept connection from {}:{}".format(address[0], address[1]))
        client_handler = Thread(target = handle_client_connection, name = "Trigger")
        client_handler.start()



def main():
    listener = Thread(target = trigger, name="TriggerListener")
    listener.start()

    send_message("10.150.92.158", "run", "foo", "ssd", "mxnet_deploy_ssd_resnet50_300_FP16_FUSED", "AWSCAM")
    # rolling
    while True:
        pass


if __name__=="__main__":
    main()