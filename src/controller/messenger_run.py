import sys
import os
from src.socket_utils import *
from threading import Thread
import time


'''
Spatial Temporal Correlation of DukeMTMC dataset
'''
corr_matrix = [
    [0, 1],
    [0, 1, 2, 4],
    [1, 2, 3],
    [2, 3],
    [1, 2, 4, 5],
    [4, 5, 6],
    [5, 6, 7],
    [0, 6, 7]
]

start_times = [
    [ 0,  5,  0,  0, 40,  0, 35, 20],
    [10,  0,  0,  0,  5,  0,  0, 10],
    [ 0,  0,  0,  5,  0,  0,  0,  0],
    [ 0,  0,  5,  0, 15,  0,  0,  0],
    [30,  5,  0, 20,  0,  5,  0, 15],
    [ 0,  0,  0,  0,  5,  0,  5,  0],
    [40,  0,  0,  0,  0,  0,  0, 10],
    [10,  5,  0,  0, 10,  0, 10,  0]
]

end_times = [
    [ 6, 80,  0,  0, 60,  0, 55, 55],
    [45,  6, 10,  0, 30,  0,  0, 30],
    [ 0, 15,  6, 40, 10,  0,  0,  0],
    [ 0,  0, 30,  6, 30,  0,  0,  0],
    [65, 55, 50, 30,  6, 50, 10, 35],
    [ 0,  0,  0,  0, 30,  6, 15,  0],
    [65,  0,  0,  0, 15, 55,  6, 30],
    [55, 20,  0,  0, 40,  0,150,  6]
]

end_times = [[f_rate * x for x in y] for y in end_times]


def send_message(*args):
    # TODO: find ip address from metadata
    conn = create_client_socket(args[0], 2)

    '''
    TODO: stop or (stop + pause) ?
    Message Format
    run    | idx | task | model | video | analysis
    switch | idx | task | model | video | analysis
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
            if res == "disappear":
                # send_message("10.150.92.158", "stop", "duke")
                # time.sleep(5)
                # send_message("10.150.243.250", "run", "duke", "ssd", "deploy_ssd_mobilenet_512", "/home/aws_cam/Desktop/local_video/00000.MTS", "True")
                pass
            else:
                send_message("10.150.92.158", "stop", "foo")
                time.sleep(5)
                send_message("10.150.243.250", "switch", "bar", "ssd", "deploy_ssd_mobilenet_512", "AWSCAM", "True")

        if ip == "10.150.243.250" and func == "ssd" and res == "stop":
            send_message("10.150.243.250", "stop", "bar")

        if ip == "10.150.243.250" and func == "ssd" and res == "switch_video":
            send_message("10.150.243.250", "switch", "bar", "ssd", "deploy_ssd_mobilenet_512", "remote.h264", "True")

        conn.send("ACK")
        conn.close()

    while True:
        print("[CRTL] Controller start listening")
        conn, address = server.accept()
        print("[CRTL] Accept connection from {}:{}".format(address[0], address[1]))
        client_handler = Thread(target = handle_client_connection, args=(conn,), name = "Trigger")
        client_handler.start()



def main():
    listener = Thread(target = trigger, name="TriggerListener")
    listener.start()

    # TEST 1
    send_message("192.168.0.185", "run", "foo", "ssd", "mxnet_deploy_ssd_resnet50_300_FP16_FUSED", 
                "/home/aws_cam/Desktop/local_video/c1_v1_m20.mp4", "True", "query_1.npy", "21")
    # send_message("10.150.243.250", "run", "bar", "ssd", "deploy_ssd_mobilenet_512", "AWSCAM", "False")

    # TEST 2
    # send_message("10.150.92.158", "run", "duke", "ssd", "deploy_ssd_mobilenet_512", "/home/aws_cam/Desktop/local_video/00000.MTS", "True")

    # rolling
    listener.join()

if __name__=="__main__":
    main()