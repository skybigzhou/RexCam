from threading import Thread, Event
import cv2
import numpy as np
import os
import time
from datetime import datetime

class LocalSave(Thread):
    def __init__(self):
        super(LocalSave, self).__init__()
        self.frame = None
        self.timestamp = ""
        self.pre_timestamp = ""
        self.stop_request = Event()

        # raise NotImplementedError("LocalSave constructor not implemented")



    def run(self):
        save_dir = '/home/aws_cam/Desktop/video/'

        '''
        if not os.path.exists(save_path):
            os.mkfifo(save_path)

        with open(save_path, 'a', os.O_NONBLOCK) as fifo_file:
            while not self.stop_request.isSet():
                try:
                    # Write the data to the FIFO file. This call will block
                    # meaning the code will come to a halt here until a consumer
                    # is available.
                    fifo_file.write(self.frame.tobytes())
                    fifo_file.flush()
                except IOError:
                    continue
        '''
        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)

        while not self.stop_request.isSet():
            try:
                if self.frame is None and self.timestamp == self.pre_timestamp:
                    continue
                cv2.imwrite(os.path.join(save_dir, self.timestamp + ".jpg"), self.frame)
                self.pre_timestamp = self.timestamp
            except IOError:
                continue



    def set_frame_data(self, frame, timestamp):
        self.frame = cv2.resize(frame, (858, 480))
        self.timestamp = timestamp


    def join(self):
        self.stop_request.set()