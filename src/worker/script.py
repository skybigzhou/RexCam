import sys
import argparse
import os
import json
import time
import numpy as np
import cv2
from six import text_type as _text_type
from threading import Thread, Event
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

# re-id query
query_dict = dict()
st_dict = dict()
et_dict = dict()
reid_threshold = 0.5

# detection-tracker switch
DT_switch = False
time_Threshold = 3

counter = 0
frame_counter = 0

'''
Input:
Output:
'''
def parse_to_modelManagement(task, frame, nickname):
    global local_address_m
    conn = Client(local_address_m, authkey = 'localModel')
    conn.send([task, frame, nickname])
    results = conn.recv()
    conn.close()
    return results


'''
Input:
Output:
'''
def cal_cosine_similarity(v1, v2):
    dot = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    cos = dot / (norm_v1 * norm_v2)
    return cos


''' 
Input: Cropped Person Image "image"
Output: Image Descriptor "image_id", return for calculating cosine similarity
'''
def reid_descriptor(image):
    image_resize = cv2.resize(image, (64, 160))
    # print(image_resize)
    results = parse_to_modelManagement('reid', image_resize, 'person-reidentification-retail-0079')
    image_id = results['embd/dim_red/conv']
    return image_id   


'''
Update tracker and convert bbox into (x, y, x+w, y+h) format
Input: Current frame "frame"
Output: tracking bbox "ret_bbox", out of tracking flag "tracking_flag" 
'''
def tracking(frame, tracker):
    ok, bbox = tracker.update(frame)
    ret_bbox = list()
    if ok:
        ret_bbox[0] = int(bbox[0])
        ret_bbox[1] = int(bbox[1])
        ret_bbox[2] = int(bbox[0] + bbox[2])
        ret_bbox[3] = int(bbox[1] + bbox[3])
    return ret_bbox, ok


def CheckExitTime(start, end, duration, FPS):
    if int(start * FPS) + duration < int(end * FPS):
        return True
    else:
        return False


# TODO: parse the input size
# def intel_process(task, source, nickname='deploy_ssd_mobilenet_512'):
'''
remote controller call: intel_process(idx)
local input call: intel_process(task, source, nickname) / intel_process(task, source)
'''
def intel_process(*args):
    descriptor_path = '/home/aws_cam/Desktop/reid_query/'

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
            model_dict[key] = "mxnet_deploy_ssd_resnet50_300_FP16_FUSED"
        else:
            model_dict[key] = args[2]
        bAnalysis[key] = "True"

    else:
        # Invalid parameters
        return

    print("Process key: " + key)
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
        local_display = LocalDisplay('480p', 'results_' + key + '.mjpeg')
        local_display.start()

        # Set the threshold for detection
        detection_threshold = 0.25
        # The height and width of the training set images
        input_dict = dict()
        input_dict['deploy_ssd_mobilenet_512'] = (512, 512)
        input_dict['mxnet_deploy_ssd_resnet50_300_FP16_FUSED'] = (300, 300)
        
        # Do inference until the lambda is killed.
        
        cap = VideoCapture(video_dict[key])
        FPS = cap.get(cv2.CAP_PROP_FPS)
        cap.set(1, int(int(st_dict[key]) * FPS))

        local_time = time.time()
        num = 0
        last = 0
        Match_identity = list()

        while CheckExitTime(int(st_dict[key]), int(et_dict[key]), num, FPS):
            # Disappear Trigger
            disappear = False

            # Get a frame from the video stream
            start_time = time.time()
            ret, frame = cap.readLastFrame()
            if not ret:
                raise Exception('Failed to get frame from the stream')
            
            # To ensure each frame analysis success set model name into a tmp parameters
            nickname = model_dict[key]
            task = task_dict[key]
            query_file = query_dict[key]

            if not bAnalysis[key] == "True":
                # Switch off
                pass
            else:
                # ranking reid_descriptor
                reid_rank = dict()
                reid_image = dict()

                # get query descriptor
                d_query = np.load(descriptor_path + query_file)

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
                input_width = input_dict[nickname][1]
                # Dictionary to be filled with labels and probabilities for MQTT
                cloud_output = {}
                image_id = 0
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
                        # cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255, 165, 20), 10)
                        
                        # Amount to offset the label/probability text above the bounding box.
                        # text_offset = 15
                        # See https://docs.opencv.org/3.4.1/d6/d6e/group__imgproc__draw.html
                        # for more information about the cv2.putText method.
                        # Method signature: image, text, origin, font face, font scale, color,
                        # and tickness
                        '''
                        cv2.putText(frame, "{}: {:.2f}%".format(output_map[obj['label']],
                                                                   obj['prob'] * 100),
                                    (xmin, ymin-text_offset),
                                    cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 165, 20), 6)
                        # Store label and probability to send to cloud
                        '''
                        cloud_output[output_map[obj['label']]] = obj['prob']

                        # start reid
                        if output_map[obj['label']] == 'person':
                            imcrop = frame[ymin:ymax, xmin:xmax]
                            '''
                            global counter
                            cv2.imwrite('/home/aws_cam/Desktop/sample/' + str(counter) + '.jpg', imcrop)
                            counter += 1
                            '''
                            if imcrop.shape[0] > 0 and imcrop.shape[1] > 0:
                                d = reid_descriptor(imcrop)
                                reid_rank[cal_cosine_similarity(d, d_query)] = image_id
                                reid_image[image_id] = (ymin, ymax, xmin, xmax, num)
                                image_id += 1

                # cv2.imwrite('/home/aws_cam/Desktop/result_{}.jpg'.format(num), frame)
                # print(reid_rank.keys())
                if reid_rank:
                    sorted_reid_rank = sorted(reid_rank.keys())
                    # print(sorted_reid_rank[-1])
                    if sorted_reid_rank[-1] > reid_threshold:
                        # cv2.imwrite('/home/aws_cam/Desktop/reid_result/' + str(num) + '.jpg', reid_image[reid_rank[sorted_reid_rank[-1]]])
                        Match_identity.append(reid_image[reid_rank[sorted_reid_rank[-1]]])
                        last = num
                num += 1
                # print("Match_identity:", Match_identity)

            # Set the next frame in the local display stream.
            cv2.putText(frame, "FPS: {:.2f}".format(1.0 / (time.time() - start_time)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 165, 20), 6)
            local_display.set_frame_data(frame)
            # Send results to the controller and Print results in local
            if not bAnalysis[key] == "True":
                pass
            else:
                pass
                '''
                if frame_counter > :
                    ctrl_ip = "192.168.0.143"
                    conn = create_client_socket(ctrl_ip, 3)
                    self_ip = "192.168.0.185"
                    conn.send("{}|{}|{}".format(self_ip, task_dict[key], "disappear"))

                    res = conn.recv(1024)
                    if res == "ACK":
                        print("[APP] Receive ACK from remote")
                        conn.close()
                '''

        last_apperance = int(st_dict[key]) + int(last / FPS) + 1
        # print("Match_identity:", Match_identity)    
        ctrl_ip = "192.168.0.143"
        conn = create_client_socket(ctrl_ip, 3)
        self_ip = "192.168.0.185"
        if Match_identity:
            conn.send("{}|{}|{}|{}|{}".format(self_ip, "True", Match_identity, num, last_apperance))
        else:
            conn.send("{}|{}|{}|{}|{}".format(self_ip, "False", "None", num, last_apperance))
        res = conn.recv(1024)
        if res == "ACK":
            print("[APP] Receive ACK from remote")
            conn.close()

    except Exception as ex:
        print("Exception:", ex)


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


class RunTimeThread(Thread):
    """
    Thread with stop() and isStop() func
    """

    def __init__(self, idx):
        super(RunTimeThread, self).__init__()
        self.idx = idx
        self._stop_event = Event()

    def run(self):
        intel_process(self.idx)

    def stop(self):
        self._stop_event.set()

    def isStop(self):
        return self._stop_event.is_set()


def ctrl_switch():
    server = create_server_socket(2)

    def handle_client_connection(conn):
        '''
        TODO: stop or (stop + pause) ?
        Message Format
        run    | idx | task | model | video | analysis | query_file | start_time | end_time
        switch | idx | task | model | video | analysis | query_file | start_time | end_time
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
                bAnalysis[idx] = msg_list[5]
                query_dict[idx] = msg_list[6]
                st_dict[idx] = msg_list[7]
                et_dict[idx] = msg_list[8]
                print("[APP] Begin to run {}".format(task_dict[idx]))
                if bAnalysis[idx] == "True":
                    print("[APP] Initial analysis on")
                else:
                    print("[APP] Initial analysis off")
                # TODO: StoppableThread
                t = RunTimeThread(idx)
                threads[idx] = t
                t.start()

            elif msg_list[0] == 'switch':
                task_dict[idx] = msg_list[2]
                model_dict[idx] = msg_list[3]
                video_dict[idx] = msg_list[4]
                x = bAnalysis[idx] = msg_list[5]
                query_dict[idx] = msg_list[6]
                st_dict[idx] = msg_list[7]
                et_dict[idx] = msg_list[8]
                print("[APP] Switch to [task: {}], [model: {}], [video: {}], [analysis: {}]".format(
                    task_dict[idx], model_dict[idx], video_dict[idx], lambda x: "on" if x == "True" else "off"))

            elif msg_list[0] == 'stop':
                # TODO: StoppableThread
                # threads[idx].stop()
                bAnalysis[idx] = "False"
                print("[APP] Stop analysis")

        conn.send("ACK")
        conn.close()

    while True:
        print("[APP] Application start listening")
        conn, address = server.accept()
        print("[APP] Accept connection from {}:{}".format(address[0], address[1]))
        client_handler = Thread(target=handle_client_connection, args=(conn,))
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
    localInput = False
    # local semantic check and run
    if localInput:
        parser = _get_parser()
        args = parser.parse_args()
        _semantic_check_and_run(args)
    else:
        ctrl_listener = Thread(target=ctrl_switch, name="MessageListener")
        ctrl_listener.start()

    # Keep main awake
    ctrl_listener.join()


if __name__ == "__main__":

    '''
    # tracking initiation
    (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
    tracker_types = ['BOOSTING', 'MIL', 'KCF', 'TLD', 'MEDIANFLOW', 'GOTURN', 'MOSSE', 'CSRT']
    tracker_type = tracker_types[2]

    global tracker
    if int(minor_ver) < 3:
        tracker = cv2.Tracker_create(tracker_type)
    else:
        if tracker_type == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        if tracker_type == 'MIL':
            tracker = cv2.TrackerMIL_create()
        if tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        if tracker_type == 'TLD':
            tracker = cv2.TrackerTLD_create()
        if tracker_type == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        if tracker_type == 'GOTURN':
            tracker = cv2.TrackerGOTURN_create()
        if tracker_type == 'MOSSE':
            tracker = cv2.TrackerMOSSE_create()
        if tracker_type == "CSRT":
            tracker = cv2.TrackerCSRT_create()
    '''

    main()