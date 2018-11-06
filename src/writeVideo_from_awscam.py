import awscam
import cv2
import numpy as np
import timeit
import time
import os

'''
cap = cv2.VideoCapture(0)
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
'''

ret, frame = awscam.getLastFrame()
if ret == False:
	print("Unable to read frame from camera")

frame_width = frame.shape[1]
frame_height = frame.shape[0]

save_path = "/home/aws_cam/Desktop/video"

out = cv2.VideoWriter(os.path.join(save_path, "output.avi"),
						cv2.cv.CV_FOURCC(*'XVID'),
						7,
						(frame_width, frame_height))

f = open(os.path.join(save_path, "output.txt"), "w")

try:
	while True:
		start_time = time.time()
		ret, frame = awscam.getLastFrame()	

		if ret == True:
			f.write("{:30}: {:20}s\n".format("AWS Get Last Frame Duration", time.time() - start_time))
			start_time = time.time()
			out.write(frame)
			f.write("{:30}: {:20}s\n".format("OpenCV write time per frame", time.time() - start_time))
		else:
			break
except KeyboardInterrupt:
	pass

# cap.release()
out.release()
cv2.destroyAllWindows()

f.close()
