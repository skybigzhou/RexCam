from threading import Thread, Event
from localSave import LocalSave
import os
import numpy as np
import cv2
import time
import awscam
from datetime import datetime

class InfiniteVideoCapture(Thread):
    def __init__(self):
        super(InfiniteVideoCapture, self).__init__()
        self.stop_request = Event()


    def run(self):
        local_save = LocalSave()
        local_save.start()

        while not self.stop_request.isSet():
            start_time = time.time()

            ret, frame = awscam.getLastFrame()
            timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H:%M:%S-%f')[:-3]
            if not ret:
                raise Exception('Failed to get frame from the stream')

            cv2.putText(frame, "FPS: {:.2f}".format(1.0 / (time.time() - start_time)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 165, 20), 6)
            local_save.set_frame_data(frame, timestamp)



    def join(self):
        self.stop_request.set()