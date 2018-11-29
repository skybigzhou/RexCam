from localDisplay import LocalDisplay
from wrapper import VideoCapture
from videoFrameStack import LocalSave
from modelManagement import *
from multiprocessing.connection import Client
import os
import json
import time
import numpy as np
import cv2


def model_switch():
    pass


def parse_to_modelManagement(task, frame, nickname):
    conn = Client(local_address, authkey = 'localModel')
    conn.send([task, frame, nickname])
    results = conn.recv()
    conn.close()
    return results


# TODO: parse the input size, remove the model_path
def intel_process(task, model_path, source, nickname='deploy_ssd_mobilenet_512'):
    try:
        import awscam
    except ImportError:
        print("WARNING: AWSCAM is not available in this device")

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
        
        # Starting Local Display for demo
        # local_display = LocalDisplay('480p', 'results.mjpeg')
        # local_display.start()
        
        controller = "/home/aws_cam/Desktop/controller.txt"
        f = open(controller, "w")
        f.write(nickname)
        f.close()

        # Set the threshold for detection
        detection_threshold = 0.25
        # The height and width of the training set images
        input_dict = dict()
        print(nickname)
        input_dict[nickname] = (512, 512)
        input_dict['mxnet_resnet50'] = (300, 300)
        
        # Do inference until the lambda is killed.
        
        cap = VideoCapture(source)
        
        while True:
            # Get a frame from the video stream
            start_time = time.time()
            ret, frame = cap.readLastFrame()
            if not ret:
                raise Exception('Failed to get frame from the stream')

            anaytics_switch = os.path.isfile(controller)
            if (not anaytics_switch):
                # Switch off
                pass
            else:
                # Switch on
                # Model switch pattern
                f = open(controller, "r")
                nickname = str(f.readline().rstrip())

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
                parsed_inference_results = parse_to_modelManagement(task, frame_resize)
                
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
                                    cv2.FONT_HERSHEY_SIMPLEX, yscale, (255, 165, 20), int(yscale*2))
                        # Store label and probability to send to cloud
                        cloud_output[output_map[obj['label']]] = obj['prob']
            # Set the next frame in the local display stream.
            cv2.putText(frame, "FPS: {:.2f}".format(1.0 / (time.time() - start_time)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, yscale, (255, 165, 20), int(yscale*2))
            # local_display.set_frame_data(frame)
            # Send results to the cloud
            if (not anaytics_switch):
                pass
            else:
                print(json.dumps(cloud_output), time.time() - start_time)

    except Exception as ex:
        print(ex)


def mxnet_process(model_path, weight_path):
    raise NotImplementedError()


def tensorflow_process(model_path):
    raise NotImplementedError()

        

