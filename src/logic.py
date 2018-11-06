#*****************************************************
#                                                    *
# Copyright 2018 Amazon.com, Inc. or its affiliates. *
# All Rights Reserved.                               *
#                                                    *
#*****************************************************
""" A sample lambda for object detection"""
from threading import Thread, Event
from localDisplay import LocalDisplay
import os
import json
import time
import numpy as np
import awscam
import cv2


def greengrass_infinite_infer_run():
    """ Entry point of the lambda function"""
    try:
        # This object detection model is implemented as single shot detector (ssd), since
        # the number of labels is small we create a dictionary that will help us convert
        # the machine labels to human readable labels.
        model_type = 'ssd'
        output_map = {1: 'aeroplane', 2: 'bicycle', 3: 'bird', 4: 'boat', 5: 'bottle', 6: 'bus',
                      7 : 'car', 8 : 'cat', 9 : 'chair', 10 : 'cow', 11 : 'dinning table',
                      12 : 'dog', 13 : 'horse', 14 : 'motorbike', 15 : 'person',
                      16 : 'pottedplant', 17 : 'sheep', 18 : 'sofa', 19 : 'train',
                      20 : 'tvmonitor'}
        # Create an IoT client for sending to messages to the cloud.
        # client = greengrasssdk.client('iot-data')
        # iot_topic = '$aws/things/{}/infer'.format(os.environ['AWS_IOT_THING_NAME'])
        # Create a local display instance that will dump the image bytes to a FIFO
        # file that the image can be rendered locally.
        local_display = LocalDisplay('480p')
        local_display.start()
        cap = cv2.VideoCapture(0)
        # The sample projects come with optimized artifacts, hence only the artifact
        # path is required.
        model_path = '/opt/awscam/artifacts/deploy_ssd_mobilenet_512.xml'
        # Load the model onto the GPU.
        # client.publish(topic=iot_topic, payload='Loading object detection model')
        model = awscam.Model(model_path, {'GPU': 1})
        # client.publish(topic=iot_topic, payload='Object detection model loaded')
        print("Object detection model loaded")
		# Set the threshold for detection
        detection_threshold = 0.25
        # The height and width of the training set images
        input_height = 512
        input_width = 512
        # Do inference until the lambda is killed.
        while True:
            # Get a frame from the video stream
            start_time = time.time()
            # ret, frame = awscam.getLastFrame()
            ret, frame = cap.read()
            if not ret:
                raise Exception('Failed to get frame from the stream')
            # Resize frame to the same size as the training set.
            frame_resize = cv2.resize(frame, (input_height, input_width))
            exists = os.path.isfile("/home/aws_cam/Desktop/controller.txt")
            if (not exists):
                pass
            else:
                # Run the images through the inference engine and parse the results using
                # the parser API, note it is possible to get the output of doInference
                # and do the parsing manually, but since it is a ssd model,
                # a simple API is provided.
                parsed_inference_results = model.parseResult(model_type,
                                                             model.doInference(frame_resize))
                # Compute the scale in order to draw bounding boxes on the full resolution
                # image.
                yscale = float(frame.shape[0])/input_height
                xscale = float(frame.shape[1])/input_width
                # Dictionary to be filled with labels and probabilities for MQTT
                cloud_output = {}
                # Get the detected objects and probabilities
                for obj in parsed_inference_results[model_type]:
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
            print(json.dumps(cloud_output), time.time() - start_time)
    except Exception as ex:
        # client.publish(topic=iot_topic, payload='Error in object detection lambda: {}'.format(ex))
		pass

if __name__=="__main__":
	greengrass_infinite_infer_run()
