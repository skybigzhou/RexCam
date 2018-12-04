from localDisplay import LocalDisplay
from wrapper import VideoCapture
from videoFrameStack import LocalSave
import os
import json
import time
import numpy as np
import cv2

'''
def _get_index(start_time, fps, timeout, duration):
    chunk_idx = int((start_time + duration) / timeout) + 1
    frame_idx = fps* start_time
    print("Loading from video tmp_{0}.h264 from frame {1} to frame {2}".format(chunk_idx, frame_idx+1, (start_time+duration)*fps))

    return chunk_idx, frame_idx
'''

#TODO: change the inference logic for local after change API
def inference_local(startTime, duration, model_path, source, nickname, task):
    try:
        import awscam
    except ImportError:
        pass

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
        
        local_display = LocalDisplay('480p', 'results_local.mjpeg')
        local_display.start()

        print("Loading Model ...")
        start_time = time.time()
        model_dict = dict()
        model_dict[nickname] = awscam.Model(model_path, {'GPU': 1})
        
        controller = "/home/aws_cam/Desktop/controller_local.txt"
        f = open(controller, "w")
        f.write(nickname)
        f.close()

        new_model_path = '/opt/awscam/artifacts/mxnet_deploy_ssd_resnet50_300_FP16_FUSED.xml'
        model_dict['mxnet_resnet50'] = awscam.Model(new_model_path, {'GPU': 1})
        print("Intel Pre-trained Object Detection Model Loaded. Time Cost: {}".format(time.time() - start_time))
        
        # Set the threshold for detection
        detection_threshold = 0.25
        # The height and width of the training set images
        input_dict = dict()
        input_dict[nickname] = (512, 512)
        input_dict['mxnet_resnet50'] = (300, 300)

        fps = 24
        timeout = 10
        
        chunk_idx, frame_idx = _get_index(startTime, fps, timeout, duration)

        file_dir = "/home/aws_cam/Desktop/local_video"
        file_name = "tmp_{}.h264".format(chunk_idx)

        cap = cv2.VideoCapture(os.path.join(file_dir, file_name))
        ret = cap.set(1, frame_idx)

        for i in xrange(fps*duration):
            start_time = time.time()
            ret, frame = cap.read()

            if not ret:
                raise Exception('Failed to get frame from the stream')

            anaytics_switch = os.path.isfile(controller)
            if (not anaytics_switch):
                pass
            else:
                f = open(controller, "r")
                model_switch = str(f.readline().rstrip())
                if model_switch not in model_dict.keys():
                    model_switch = 'mxnet_resnet50'
                # Run the images through the inference engine and parse the results using
                # the parser API, note it is possible to get the output of doInference
                # and do the parsing manually, but since it is a ssd model,
                # a simple API is provided.
                frame_resize = cv2.resize(frame, input_dict[model_switch])
                parsed_inference_results = model_dict[model_switch].parseResult(task,
                                                             model_dict[model_switch].doInference(frame_resize))
                # Compute the scale in order to draw bounding boxes on the full resolution
                # image.
                yscale = float(frame.shape[0])/input_dict[model_switch][0]
                xscale = float(frame.shape[1])/input_dict[model_switch][1]
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
            # cv2.putText(frame, "FPS: {:.2f}".format(1.0 / (time.time() - start_time)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, yscale, (255, 165, 20), int(yscale*2))
            cv2.putText(frame, "Frame Number: " + str(frame_idx+i+1), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, yscale, (255, 165, 20), int(yscale*2))
            local_display.set_frame_data(frame)

            if (not anaytics_switch):
                pass
            else:
                print(json.dumps(cloud_output), time.time() - start_time, frame_idx+i+1)

    except Exception as ex:
        print(ex)    






