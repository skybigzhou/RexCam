import sys
import argparse
import os
import cv2
from videoFrameStack import LocalSave
from threading import Thread, Event
from six import text_type as _text_type
from multiprocessing.connection import Listener, Client
import socket
from socket_utils import *

global local_address_d
local_address_d = ('localhost', 6001)

local_dir = "/home/aws_cam/Desktop/local_video"
remote_dir = "/home/aws_cam/Desktop/remote_video"


def _get_parser():
    parser = argparse.ArgumentParser(description="Start Data Management with parameters")

    parser.add_argument(
        "--source", "-s",
        type=_text_type,
        default="AWSCAM",
        choices=['AWSCAM', 'WEBCAM', 'Local'],
        help="Video streaming source")

    parser.add_argument(
        "--cTimeout", "-c",
        type=int,
        default=10,
        help="Timeout for saving video stream in a chunk")

    parser.add_argument(
        "--overlap", "-l",
        type=int,
        default=10,
        help="Overlap time for two chunk solving non I-frame problem")

    parser.add_argument(
        "--totalTimeout", "-t",
        type=int,
        default=10*60,
        help="Total timeout for Data Management process")

    return parser


#TODO: shorten the sending data
def min_send_data(name):
    return name


def remote_listener():
    server = create_server_socket()

    def handle_client_connection(conn):
        video_id = conn.recv(1024)
        print("Receive request for {}".format(video_id))

        #TODO: get model_path from metadata
        data = min_send_data(video_id)
        data_path = os.path.join(local_dir, video_id)
        #TODO: check send model

        send_file(conn, data_path)
        #TODO: update metadata

        conn.send('ACK')
        conn.close()

    while True:
        print("[DATA] Remote Listener start listening")
        conn, address = server.accept()
        print("Accept connection from {}:{}".format(address[0], address[1]))
        client_handler = Thread(target=handle_client_connection, args=(conn,), name= "remoteListenerDataWorker")
        client_handler.start()


def fetch_remote_model(video_id):
    #TODO: address = ?
    ip = 'localhost'
    conn = create_client_socket(ip)
    conn.send(video_id)

    #TODO: check file recv
    data_path = os.path.join(remote_dir, video_id)
    recv_file(conn, data_path)
    
    response = conn.recv(1024)
    if response == "ACK":
        print("Receive ACK from remote")
        conn.close()


def local_listener():
    listener = Listener(local_address_d, authkey="localData")
    while True:
        conn = listener.accept()
        print("[DATA] connection accepted from", listener.last_accepted)
        msg = conn.recv()

        # TODO: check end validation
        assert isinstance(msg, list) and len(msg) == 4
        video_id = msg[0]
        begin = msg[1]
        end = msg[2]
        fps = msg[3] # Recently fps can only be 24

        if not video_id == "local.h264":
            fetch_remote_data(video_id)

        cap = cv2.VideoCapture(os.path.join(local_dir, video_id))
        frame_id = begin * fps
        ret = cap.set(1, frame_id)

        if begin == end:
            ret, frame = cap.read()
            conn.send([frame])
            conn.close()
        else:
            frame_list = list()
            for i in xrange((end-begin)*fps):
                ret, frame = cap.read()
                frame_list.append(frame)

            conn.send(frame_list)
            conn.close()

    listener.close()


def start_data_management(args):
    chunk_timeout = args.cTimeout
    timeout = args.totalTimeout
    overlap = args.overlap
    source = args.source

    if source == "Local":
        print("Read video from disk will not turn on the Data Management")
    else:
        print("Data Management Local Save Starting ...")

    local_save = LocalSave(source, timeout, chunk_timeout, overlap)
    local_save.start()

    t_local = Thread(target=local_listener, name="localListenerData")
    t_local.start()
    t_remote = Thread(target=remote_listener, name="remoteListenerData")
    t_remote.start()

    local_save.stop(timeout)

    t_local.join()
    t_remote.join()


def main():
    parser = _get_parser()
    args = parser.parse_args()
    start_data_management(args)


if __name__ == "__main__":
    main()