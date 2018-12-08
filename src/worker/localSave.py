from threading import Thread, Event
import cv2
import numpy as np
import os
import time
import json

class LocalSave(Thread):
    '''
    
    '''
    def __init__(self):
        super(LocalSave, self).__init__()
        # Initialize the default image to be a white canvas. Clients
        # will update the image when ready.
        self.frame = cv2.imencode('.jpg', 255*np.ones([640, 480, 3]))[1]
        self.counter = 0
        self.change = False
        self.first = True
        self.timestamp = ""
        self.stop_request = Event()


    def _update_metadata(self, save_dir, test):
        """Dummy Solution"""
        if test:
            start_time = time.time()
        
        data_file = os.path.join(save_dir, 'metadata.txt')
        
        '''
        if self.first:
            with open(data_file, 'w', os.O_NONBLOCK) as f:
                json.dump({self.timestamp: self.counter}, f)
            self.first = False
        else:
            data = dict()
            with open(data_file, 'r', os.O_NONBLOCK) as f:
                str_read = f.read()
                data = json.loads(str_read)
        
            with open(data_file, 'w', os.O_NONBLOCK) as f:
                data[self.timestamp] = self.counter
                json.dump(data, f)
        '''
        with open(data_file, 'a', os.O_NONBLOCK) as f:
            f.write(str(self.timestamp) + "," + str(self.counter)+ "\n")
        
        if test:
            print(time.time() - start_time)
    


    def run(self):
        # TODO: Maintain a MetaData
        save_dir = '/home/aws_cam/Desktop/video/'

        if not os.path.isdir(save_dir):
            os.mkdir(save_dir)

        while not self.stop_request.isSet():
            try:
                if not self.change:
                    continue
                test = False
                cv2.imwrite(os.path.join(save_dir, "frame_" + str(self.counter) + ".jpg"), self.frame)
                self._update_metadata(save_dir, test)
                self.counter += 1
            except IOError:
                continue


    def set_frame_data(self, frame, timestamp):
        self.frame = frame
        self.change = True
        self.timestamp = timestamp


    def join(self):
        self.stop_request.set()
