import sys
import argparse
import os
import time
try:
    import awscam
except ImportError:
    print("WARNING: AWSCAM is not available in this device")


class Model_Dict(object):

    def __init__(self):
        self._dict = dict()
        
    def get_all_dict(self):
        return self._dict

    def get_dict(self, key):
        return self._dict[key]

    def set_dict(self, key):
        self._dict[key.rsplit('/', 1)[-1]] = awscam.Model(key, {'GPU': 1})
        


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

    model_dict = Model_Dict()

    for i in xrange(models_num):
        try:
            start_time = time.time()
            model_dict.set_dict(models_path[i])
            print("Intel Pre-trained Object Detection Model {0} Loaded. Time Cost: {1}".format(
                models_path[i].rsplit('/', 1)[-1], time.time() - start_time))

        except Exception as ex:
            print(ex)


def main():
    parser = _get_parser()
    args = parser.parse_args()
    preload_models(args)


if __name__=="__main__":
    main()