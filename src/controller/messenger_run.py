import sys
import os
from src.socket_utils import *
from threading import Thread
import time

# Match cam_id with ip_address
cam_ip = {1:"192.168.0.185", 2:"192.168.0.185", 3:"192.168.0.185", 4:"192.168.0.185", 5:"192.168.0.185"}
video_dict = {1:"/home/aws_cam/Desktop/local_video/c1_v1_m20.mp4",
              2:"/home/aws_cam/Desktop/local_video/c4_v2_m20.mp4",
              3:"/home/aws_cam/Desktop/local_video/c2_v3_m20.mp4",
              4:"/home/aws_cam/Desktop/local_video/c3_v4_m20.mp4",
              5:"/home/aws_cam/Desktop/local_video/c5_v5_m20.mp4"}

model = "mxnet_deploy_ssd_resnet50_300_FP16_FUSED"
global total_frames
global global_query

corr_matrix = [
        [1, 2],
        [1, 2, 3, 4],
        [2, 3, 5],
        [2, 4, 5],
        [3, 4, 5],
    ]

start_times = [
    [ 0, 10, 20,  0, 30],
    [15,  0,  0, 20,  5],
    [35,  5,  0, 10,  0],
    [ 0,  0, 10,  0, 25],
    [40,  5,  0,  0,  0],
]

end_times = [
    [ 6, 45, 50,  0, 70],
    [40,  6, 60, 35, 25],
    [45, 20,  6, 25, 10],
    [ 0,  0, 25,  6, 60],
    [60, 20, 10,  0,  6],
]

def get_id_from_ip(ip):
    return cam_ip.keys()[cam_ip.values().index(ip)]


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
        # msg format = |...ip...|..True..|..res..|..duration..|..last_apperance..|
        # msg format = |...ip...|..False..|..None..|..duration..|..last_apperance..|
        msg = conn.recv(8192)
        # print(msg)

        ip, found, res, duration, last_apperance = msg.split("|")
        global total_frames
        total_frames += int(duration)
        print(total_frames)
        # print("[CRTL] Get Results {0} from [ip:{1}]. Found or not:{2} ...".format(res, ip, func))
        cam_id = get_id_from_ip(ip)

        conn.send("ACK")
        conn.close()

        # deal with instruction
        if found == "True":
            for corr_cam_id in corr_matrix[cam_id - 1]:
                start_time = int(last_apperance) + start_times[cam_id - 1][corr_cam_id - 1]
                end_time = int(last_apperance) + end_times[cam_id - 1][corr_cam_id - 1]
                send_message(cam_ip[corr_cam_id], "run", str(corr_cam_id) + "_" + str(start_time), "ssd", model, 
                                video_dict[corr_cam_id], "True", global_query, str(start_time), str(end_time))
            
        

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
    '''
    send_message(cam_ip[1], "run", "foo", "ssd", model, 
                video_dict[1], "True", "query_1.npy", "21", "")
    '''
    # send_message("10.150.243.250", "run", "bar", "ssd", "deploy_ssd_mobilenet_512", "AWSCAM", "False")

    # TEST 2
    # send_message("10.150.92.158", "run", "duke", "ssd", "deploy_ssd_mobilenet_512", "/home/aws_cam/Desktop/local_video/00000.MTS", "True")
    query_list = {(1, "21", "query_1.npy")}

    for query in query_list:
        global total_frames
        global global_query
        total_frames = 0

        cam_id = query[0]
        frame_id = query[1]
        global_query = query[2]
        start_time = int(frame_id) + start_times[cam_id][cam_id]
        end_time = int(frame_id) + end_times[cam_id][cam_id]
        send_message(cam_ip[cam_id], "run", "foo", "ssd", model, video_dict[cam_id], "True", global_query, str(start_time), str(end_time))

    listener.join()

if __name__=="__main__":
    main()