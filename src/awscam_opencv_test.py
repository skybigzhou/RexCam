import awscam
import cv2
import timeit
import time

def main():
	# start_time = time.time()
	# cap = cv2.VideoCapture('/home/aws_cam/Desktop/video/output.avi')
	# print("CV2 VideoCapture Initial: {}".format(time.time() - start_time))	

	ret, frame = awscam.getLastFrame()
	# ret, frame = cap.read()	

	aws_total_time = 0.0
	# cv2_total_time = 0.0

	for x in range(0, 100):
		ret, frame = awscam.getLastFrame()
		start_time = time.time()
		cv2.imwrite('/home/aws_cam/Desktop/video/{}.jpg'.format(x), frame)
		aws_time = time.time() - start_time
		aws_total_time += aws_time
	
		'''

		start_time = time.time()
		ret, frame = cap.read()
		cv2_time = time.time() - start_time
		cv2_total_time += cv2_time
		print("AWS_GetLastFrame vs OpenCV Read From Local File: {:18} vs {:18}".format(aws_time, cv2_time))
		
		'''
	print("AWS_AVERAGE {}".format(aws_total_time/100))
	# print("CV2_AVERAGE {}".format(cv2_total_time/100))
	
if __name__ == "__main__":
	main()
