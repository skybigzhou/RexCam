import sys
import argparse
import os
from videoFrameStack import LocalSave
from threading import Thread, Event
from six import text_type as _text_type


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
        default=60,
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

    t_local = Thread(target=)
    t_local.start()
    t_remote = 
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