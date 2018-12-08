import sys
import argparse
import os
import inference_local
from six import text_type as _text_type


def _get_parser():
    parser = argparse.ArgumentParser(description="Please Input Local Inference Info")

    parser.add_argument(
        "--startTime", "-st",
        type=int,
        default=0,
        help="Start time for local inference")

    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=0,
        help="Duration for local inference")

    '''
    parser.add_argument(
        "--framework", "-f",
        type=_text_type,
        choices=['tensorflow', 'tf', 'mxnet', 'mx', 'intel_mo_IR'],
        required=True,
        help="Identify your model framework (deeplens only support intel_mo_IR and mx/tf with cpu)")


    '''
    parser.add_argument(
        "--modelTask", "-t",
        type=_text_type,
        help="Identify your model task (recently only support Object Detection/ Classification)")


    parser.add_argument(
        "--modelPath", "-mp",
        type=_text_type,
        required=True,
        help="Path to the pre-trained model file (e.g. mxnet: MODELPATH-symbol.json and MODELPATH-0000.params, tensorflow: MODELPATH.pb, Intel IR: MODELPATH.xml and MODELPATH.bin)")

    parser.add_argument(
        "--labelPath", "-lp",
        type=_text_type,
        help="Path to the label file (detect .json file or python dict())")

    parser.add_argument(
        '--nickName', '-n',
        type=_text_type,
        help="Model Nick Name, used for control model switch")

    parser.add_argument(
        "--source", "-s",
        type=_text_type,
        default="WEBCAM",
        help="Identify video stream source, either from \'WEBCAM\', \'AWSCAM\' or Path to the local file")

    return parser


def _semantic_check_and_run(args):
    start_time = args.startTime
    duration = args.duration
    model_path = str(args.modelPath) + ".xml"
    source = str(args.source)
    if args.nickName:
        nickname = args.nickName
    else:
        nickname = "User_Model_0"

    if args.modelTask:
        task = str(args.modelTask)

    print("Start time: {}s".format(start_time))
    print("Duration: {}s".format(duration))
    inference_local.inference_local(start_time, duration, model_path, source, nickname, task)



def main():
    parser = _get_parser()
    args = parser.parse_args()
    _semantic_check_and_run(args)


if __name__ == "__main__":
    main()