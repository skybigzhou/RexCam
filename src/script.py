import sys
import argparse
import os
import inference
from six import text_type as _text_type



def _get_parser():
    parser = argparse.ArgumentParser(description="Please Input Inference Model Info")

    parser.add_argument(
        "--framework", "-f",
        type=_text_type,
        choices=['tensorflow', 'tf', 'mxnet', 'mx', 'intel_mo_IR'],
        required=True,
        help="Identify your model framework (deeplens only support intel_mo_IR and mx/tf with cpu)")

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
    framework = args.framework
    model_path = args.modelPath
    source = str(args.source)
    if args.nickName:
        nickname = args.nickName
    else:
        nickname = "User_Model_0"

    if "." in model_path:
        reply = raw_input("WARNING: file suffix should not be included, would you like to continue(y/n): ")
        if not (reply.lower() == "y" or reply.lower() == "yes"):
            return

    if args.modelTask:
        task = str(args.modelTask)

    if args.framework == "tf" or args.framework == "tensorflow":
        inference.tensorflow_process(str(model_path + ".pb"))

    elif args.framework == "mx" or args.framework == "mxnet":
        model_path = str(model_path + "-symbol.json")
        weight_path = str(model_path + "-0000.params")
        inference.mxnet_process(model_path, weight_path)

    elif args.framework == "intel_mo_IR":
        try:
            inference.intel_process(task, str(model_path + ".xml"), source, nickname)
        except Exception:
            print("Error: Task Not Clarified")

    #TODO: convert input label file
    if args.labelPath:
        pass
    


def main():
    parser = _get_parser()
    args = parser.parse_args()

    _semantic_check_and_run(args)



if __name__ == "__main__":
    main()