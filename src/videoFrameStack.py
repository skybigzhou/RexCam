from threading import Thread, Event
import os
import numpy as np
import cv2
import time
import awscam
from datetime import datetime
import subprocess


class Command(object):
    def __init__(self, cmd, name):
        self.cmd = cmd
        self.process = None
        self.thread = None
        self.name = name


    def run(self):
        def h264Save():
            print("Start Saving in a New Video Stream {}".format(self.name))
            self.process = subprocess.Popen(self.cmd, shell=True)
            self.process.communicate()
            print("Saving Ended {}".format(self.name))

        self.thread = Thread(target = h264Save)
        self.thread.start()


    def join(self, timeout):
        self.thread.join(timeout)
        if self.process and self.thread.is_alive():
            print("Timeout Process Terminated")
            # self.process.terminate()
            self.thread.join()
        # print(self.process.returncode)



class LocalSave(Thread):
    '''
    Instance of Data Management. When Device turn on, the Data Management
    should Infinitely read from video source (AWSCAM/WEBCAM) then feed it
    to the localSave.
    In this case, the when the instance is on, it will also call the local
    saving instance thread on to ensure parallelize fetching video feed
    and write to the disk.
    '''
    def __init__(self, source, timeout, chunk_timeout=60, overlap=10):
        super(LocalSave, self).__init__()
        self.stop_request = Event()
        self.counter = 0
        self.source = source
        self.ttimeout = timeout
        self.timeout = chunk_timeout
        self.overlap = overlap
        self.last_command = None


    def run(self):
        '''
        local_save = LocalSave()
        local_save.start()
        '''
        command = Command("timeout {} cat /opt/awscam/out/ch1_out.h264 > /home/aws_cam/Desktop/local_video/out.h264".format(self.ttimeout), "out.h264")
        command.run()

        if self.source == "AWSCAM":
            while not self.stop_request.isSet():
                
                time.sleep(self.timeout)
                command = Command("cp /home/aws_cam/Desktop/local_video/out.h264 /home/aws_cam/Desktop/local_video/tmp_{1}.h264".format(
                                self.timeout, self.counter), "tmp_{}.h264".format(self.counter))

                command.run()
                
                self.counter += 1
                

                '''
                if self.last_command:
                    self.last_command.join(self.overlap)
                    self.counter += 1
                    self.last_command = command
                    time.sleep(self.timeout - self.overlap * 2)
                else:
                    self.counter += 1
                    self.last_command = command
                    time.sleep(self.timeout - self.overlap)
                '''
        else:
            raise NotImplementedError("WEBCAM is not supported for local save yet")


        '''
        while not self.stop_request.isSet():
            ret, frame = awscam.getLastFrame()
            # timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H:%M:%S-%f')[:-3]
            timestamp = time.time()
            
            if not ret:
                raise Exception('Failed to get frame from the stream')

            # cv2.putText(frame, "FPS: {:.2f}".format(1.0 / (time.time() - start_time)), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 165, 20), 6)
            local_save.set_frame_data(frame, timestamp)
        '''


    def stop(self, timeout):
        time.sleep(timeout)
        self.stop_request.set()
