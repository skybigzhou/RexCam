import sys
import argparse
import os
import json
import time
import numpy as np
import cv2
from six import text_type as _text_type
from threading import Thread
from src.socket_utils import *
from localDisplay import LocalDisplay
from wrapper import VideoCapture
from videoFrameStack import LocalSave
from modelManagement import local_address_m
from multiprocessing.connection import Client


# Control Params: 
model_dict = dict()
video_dict = dict()
task_dict = dict()
bAnalysis = dict()

# Thread Pool
threads = dict()


def parse_to_modelManagement(task, frame, nickname):
    global local_address_m
    conn = Client(local_address_m, authkey = 'localModel')
    conn.send([task, frame, nickname])
    results = conn.recv()
    conn.close()
    return results


# TODO: parse the input size
# def intel_process(task, source, nickname='deploy_ssd_mobilenet_512'):
'''
remote controller call: intel_process(idx)
local input call: intel_process(task, source, nickname) / intel_process(task, source)
'''
def intel_process(*args):
    # Merge different parameter format and setup process $KEY$
    key = ""
    if len(args) == 1:
        # Case 1: receive remote instruction, other initial process has done when message received (For quick switch)
        key = args[0]

    elif len(args) == 2 or len(args) == 3:
        # Case 2: local instruction with default model
        # Case 3: local instruction with all parameters
        key = "local"
        task_dict[key], video_dict[key] = (args[0], args[1])
        if len(args) == 2:
            # By default
            model_dict[key] = "deploy_ssd_mobilenet_512"
        else:
            model_dict[key] = args[2]
        bAnalysis[key] = True

    else:
        # Invalid parameters
        return

    """ Entry point of the lambda function"""
    try:
        # This object detection model is implemented as single shot detector (ssd), since
        # the number of labels is small we create a dictionary that will help us convert
        # the machine labels to human readable labels.
        output_map = {1: 'aeroplane', 2: 'bicycle', 3: 'bird', 4: 'boat', 5: 'bottle', 6: 'bus',
                      7 : 'car', 8 : 'cat', 9 : 'chair', 10 : 'cow', 11 : 'dinning table',
                      12 : 'dog', 13 : 'horse', 14 : 'motorbike', 15 : 'person',
                      16 : 'pottedplant', 17 : 'sheep', 18 : 'sofa', 19 : 'train',
                      20 : 'tvmonitor'}
        
        # Create a local display instance that will dump the image bytes to a FIFO
        # file that the image can be rendered locally.
        
        # Start Local Display for demo
        local_display = LocalDisplay('480p', 'results.mjpeg')
        local_display.start()

        # Set the threshold for detection
        detection_threshold = 0.25
        # The height and width of the training set images
        input_dict = dict()
        input_dict['deploy_ssd_mobilenet_512'] = (512, 512)
        input_dict['mxnet_deploy_ssd_resnet50_300_FP16_FUSED'] = (300, 300)
        
        # Do inference until the lambda is killed.
        
        cap = VideoCapture(video_dict[key])
        
        while True:
            # Get a frame from the video stream
            start_time = time.time()
            ret, frame = cap.readLastFrame()
            if not ret:
                raise Exception('Failed to get frame from the stream')
            # To ensure each frame analysis success set model name into a tmp parameters
            nickname = model_dict[key]

            if (not bAnalysis[key]):
                # Switch off
                pass
            else:
                # Note that $KEY$ should not appear in this condition
                # Switch on
                # Resize frame to the same size as the training set.
                frame_resize = cv2.resize(frame, input_dict[nickname])

                # Run the images through the inference engine and parse the results using
                # the parser API, note it is possible to get the output of doInference
                # and do the parsing manually, but since it is a ssd model,
                # a simple API is provided.
                # Change the model inference API by send frame to model Management
                '''
                AWSCAM API
                parsed_inference_results = model.parseResult(task,
                                                             model.doInference(frame_resize))
                '''
                parsed_inference_results = parse_to_modelManagement(task, frame_resize, nickname)
                
                # Compute the scale in order to draw bounding boxes on the full resolution
                # image.
                yscale = float(frame.shape[0])/input_dict[nickname][0]
                xscale = float(frame.shape[1])/input_dict[nickname][1]
                # Dictionary to be filled with labels and probabilities for MQTT
                cloud_output = {}
                # Get the detected objects and probabilities
                for obj in parsed_inference_results[task]:
                    if obj['prob'] > detection_threshold:
                        # Add bounding boxes to full resolution frame
                        xmin = int(xscale * obj['xmin'])
                               # + int((obj['xmin'] - input_width/2) + input_width/2)
                        ymin = int(yscale * obj['ymin'])
                        xmax = int(xscale * obj['xmax']) 
                               # + int((obj['xmax'] - input_width/2) + input_width/2)
                        ymax = int(yscale * obj['ymax'])
                        # See https://docs.opencv.org/3.4.1/d6/d6e/group__imgproc__draw.html
                        # for more information about the cv2.rectangle method.
                        # Method signature: image, point1, point2, color, and tickness.
                        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255, 165, 20), 10)
                        # Amount to offset the label/probability text above the bounding box.
                        text_offset = 15
                        # See https://docs.opencv.org/3.4.1/d6/d6e/group__imgproc__draw.html
                        # for more information about the cv2.putText method.
                        # Method signature: image, text, origin, font face, font scale, color,
                        # and tickness
                        cv2.putText(frame, "{}: {:.2f}%".format(output_map[obj['label']],
                                                                   obj['prob'] * 100),
                                    (xmin, ymin-text_offset),
                                    cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 165, 20), 6)
                        # Store label and probability to send to cloud
                        cloud_output[output_map[obj['label']]] = obj['prob']
            # Set the next frame in the local display stream.
            cv2.putText(frame, "FPS: {:.2f}".format(1.0 / (time.time() - start_time)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 165, 20), 6)
            local_display.set_frame_data(frame)
            # Send results to the cloud
            if (not bAnalysis[key]):
                pass
            else:
                print(json.dumps(cloud_output), time.time() - start_time)

    except Exception as ex:
        print(ex)


def mxnet_process(model_path, weight_path):
    raise NotImplementedError()


def tensorflow_process(model_path):
    raise NotImplementedError()


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


def ctrl_switch():
    server = create_server_socket(3)

    def handle_client_connection(conn):
        # msg format = ?
        '''
        TODO: stop or (stop, pause) ?
        run    | idx | task | model | video
        switch | idx | task | model | video
        stop   | idx
        '''
        msg = conn.recv(1024)
        print("[APP] Deal with message ...")

        # TODO: Change Control Params [Message Split with '|']
        msg_list = msg.split('|')
        if len(msg_list) > 1:
            idx = msg_list[1]
            if msg_list[0] == 'run':
                task_dict[idx] = msg_list[2]
                model_dict[idx] = msg_list[3]
                video_dict[idx] = msg_list[4]
                # TODO: StoppableThread
                # t = Thread(target=intel_process, args=(idx,))
                # t.start()
                # threads[idx] = t

            elif msg_list[0] == 'switch':
                task_dict[idx] = msg_list[2]
                model_dict[idx] = msg_list[3]
                video_dict[idx] = msg_list[4]

            elif msg_list[0] == 'stop':
                # TODO: StoppableThread
                # threads[idx].stop()
                pass

        conn.send("ACK")
        conn.close()

    while True:
        print("[APP] Application start listening")
        conn, address = server.accept()
        print("[APP] Accept connection from {}:{}".format(address[0], address[1]))
        client_handler = Thread(target=handle_client_connection)
        client_handler.start()


def _semantic_check_and_run(args):
    framework = args.framework
    # model_path = args.modelPath
    source = str(args.source)
    
    if args.modelTask:
        task = str(args.modelTask)

    '''
    # This process has been removed due to model management
    if "." in model_path:
        reply = raw_input("WARNING: file suffix should not be included, would you like to continue(y/n): ")
        if not (reply.lower() == "y" or reply.lower() == "yes"):
            return

    if args.framework == "tf" or args.framework == "tensorflow":
        tensorflow_process(str(model_path + ".pb"))

    elif args.framework == "mx" or args.framework == "mxnet":
        model_path = str(model_path + "-symbol.json")
        weight_path = str(model_path + "-0000.params")
        mxnet_process(model_path, weight_path)

    elif args.framework == "intel_mo_IR":
        try:
            if args.nickName:
                intel_process(task, str(model_path + ".xml"), source, str(args.nickName))
            else:
                intel_process(task, str(model_path + ".xml"), source)

        except Exception as ex:
            print("Exception {}".format(ex))
    '''

    try:
        if args.nickName:
            intel_process(task, source, str(args.nickName))
        else:
            intel_process(task, source)

    except Exception as ex:
        print("Exception {}".format(ex))

    #TODO: convert input label file
    if args.labelPath:
        pass


def main():
    localInput = True
    # local semantic check and run
    if localInput == True:
        parser = _get_parser()
        args = parser.parse_args()
        _semantic_check_and_run(args)
    else:
        ctrl_listener = Thread(target=ctrl_switch, name="MessageListener")
        ctrl_listener.start()

    # Keep main awake
    timeout = 10*60
    time.sleep(timeout)


if __name__ == "__main__":
    main()