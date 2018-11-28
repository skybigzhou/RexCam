import sys
import argparse
import os
import time
import pprint
try:
    import awscam
except ImportError:
    print("WARNING: AWSCAM is not available in this device")
from multiprocessing.connection import Listener, Client
from threading import Thread


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
        print("Want get model ...")
        print(self._dict[key][1])
        return self._dict[key][1]

    def set_dict(self, key, value):
        self._dict[key] = [value, awscam.Model(value, {'GPU': 1})]

model_dict = Model_Dict()


def _get_parser():
    parser = argparse.ArgumentParser(description="Start Model Management- A preload model pool for user model switch")

    parser.add_argument(
        "--models_path", "-mps",
        nargs="*",
        required=True,
        help="Declare all the models path you want to preload")

    return parser


def preload_models(args):
    models_path = args.models_path
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

    pprint.pprint(model_dict.get_all_dict())


def local_listener():
    local_address = ('localhost', 6000)
    listener = Listener(local_address, authkey="localModel")
    conn = listener.accept()
    print("connection accepted from", listener.last_accepted)
    while True:
        msg = conn.recv()

        if msg.lower() == "disconnected":
            conn.close()
            break
        else:
            segment = msg.split()
            if len(segment) != 2:
                print("Message format invalid. Please resend valid message to get model")
            else:
                pass

    listener.close()


def main():
    parser = _get_parser()
    args = parser.parse_args()
    preload_models(args)

    t = Thread(target=local_listener, name="ListenerThread")
    t.start()


if __name__=="__main__":
    main()