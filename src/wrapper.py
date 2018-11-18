import cv2
import time
import json
import os

class VideoCapture():
    """
    """
    def __init__(self, source="WEBCAM"):
        self.source = source
        self.start_time = time.time()
        if self.source == "AWSCAM":
            self.cap = cv2.VideoCapture("/tmp/save.mjpeg")
        elif self.source == "WEBCAM":
            self.cap = cv2.VideoCapture(0)
        else:
            self.cap = cv2.VideoCapture(source)

        # raise NotImplementedError("Constructor Not Implemented Yet")


    def readFrameByTime(self, timestamp):
        idx = int(timestamp - self.start_time)
        self.cap.set(1, idx)
        ret, frame = self.cap.read()

        return (ret, frame)

        raise NotImplementedError("Read Frame Through Timestamp Not Implemented Yet")


    def readFrameByPeriod(self, begin, end, fps):
        idx_b = int(begin - self.start_time)
        idx_e = int(end - self.start_time)
        ret_frame = []
        self.cap.set(1, idx)
        for i in xrange(idx_b, idx_e):
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to get frame from the stream")
                return None
            else:
                ret_frame.append(frame)

        return (ret, ret_frame)

        raise NotImplementedError("Read Frame Through Time Period Not Implemented Yet")


    def readLastFrame(self):
        '''
        source AWSCAM     : 
        source WEBCAM     :
        source localFile  : 
        '''

        # READ FROM AWSCAM OR WEBCAM
        
        if self.source == "AWSCAM":
            import awscam
            ret, frame = awscam.getLastFrame()
            return (ret, frame)

        elif self.source == "WEBCAM":
            ret, frame = self.cap.read()
            return (ret, frame)

        else:
            pass
        

        # READ FROM LOCAL DISK WITH METADATA
        ''' 
        save_dir = "/home/aws_cam/Desktop/video"
        metadata = os.path.join(save_dir, "metadata.txt")
        num = float(time.time())
        
        data = dict()
        with open(metadata, "r", os.O_NONBLOCK) as f:
            lines = f.readlines()
            for line in lines:
                line = (line.strip()).split(',')
                data[line[0]] = line[1]

        start_time = time.time()
        ans = data[num] if num in data.keys() else data[min(data.keys(), key=lambda k: abs(float(k)-num))]
        ret = True
        frame = cv2.imread(os.path.join(save_dir, "frame_" + str(ans) + ".jpg"), 1)
        print(ans, time.time() - start_time)

        return (ret, frame)
        '''
        
        raise NotImplementedError("Local file read last frame not defined.")




