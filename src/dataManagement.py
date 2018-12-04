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
            raise NotImplementedError("Cannot fetch data from remote")

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


def remote_listener():
    pass


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

    '''
    t_local = Thread(target=local_listener, name="localListenerData")
    t_local.start()
    t_remote = Thread(target=remote_listener, name="remoteListenerData")
    t_remote.start()
    '''
    local_save.stop(timeout)
    '''
    t_local.join()
    t_remote.join()
    '''

def main():
    parser = _get_parser()
    args = parser.parse_args()
    start_data_management(args)


if __name__ == "__main__":
    main()