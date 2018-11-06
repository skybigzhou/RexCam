import cv2
import time


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
        if self.source == "AWSCAM":
            import awscam
            #TODO: check awscam.getLastFrame()
            ret, frame = awscam.getLastFrame()
            return (ret, frame)

        else:
            #TODO: check opencv.VideoCapture.read()
            ret, frame = self.cap.read()
            return (ret, frame)

        raise NotImplementedError("Read Last Frame Not Implemented Yet")
