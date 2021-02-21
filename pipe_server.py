import time
import win32pipe, win32file
import threading

from datetime import datetime

from tracker.centroidtracker import CentroidTracker
from tracker.trackableobject import TrackableObject
from imutils.video import FPS
import imutils

import cv2
import dlib
import sys
import numpy as np
np.set_printoptions(threshold=sys.maxsize)
import logs

log = logs.createLogs("username")

global i
i = 0

global frame
frame = np.array([])

net = cv2.dnn.readNetFromCaffe("mobilenet_ssd/MobileNetSSD_deploy.prototxt",
 "mobilenet_ssd/MobileNetSSD_deploy.caffemodel")

# instantiate our centroid tracker, then initialize a list to store
# each of our dlib correlation trackers, followed by a dictionary to
# map each unique object ID to a TrackableObject
ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
trackers = []
trackableObjects = {}

# initialize the total number of frames processed thus far, along
# with the total number of objects that have moved either up or down
# totalFrames = 0
# totalDown = 0
# totalUp = 0

# start the frames per second throughput estimator
fps = FPS().start()

# video = cv2.VideoCapture(0)
video = cv2.VideoCapture("videos/example_01.mp4")


CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
	"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
	"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
	"sofa", "train", "tvmonitor"]

global totalFrames
totalFrames = 0
global totalDown
totalDown = 0
global totalUp
totalUp = 0

def gen():

	global totalFrames
	totalFrames = 0
	global totalDown
	totalDown = 0
	global totalUp
	totalUp = 0

	global frame

	while True:
		success, frame = video.read()
		# print(success)
		if success == False:
			print("no frame")
			pass

		# resize the frame to have a maximum width of 500 pixels (the
		# less data we have, the faster we can process it), then convert
		# the frame from BGR to RGB for dlib
		frame = imutils.resize(frame, width=500)
		# frame = imutils.rotate_bound(frame, 90)
		rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


		# initialize the current status along with our list of bounding
		# box rectangles returned by either (1) our object detector or
		# (2) the correlation trackers
		status = "Waiting"
		rects = []

		# check to see if we should run a more computationally expensive
		# object detection method to aid our tracker
		if totalFrames % 30 == 0:
			# set the status and initialize our new set of object trackers
			status = "Detecting"
			trackers = []

			(H, W) = frame.shape[:2]

			# convert the frame to a blob and pass the blob through the
			# network and obtain the detections
			blob = cv2.dnn.blobFromImage(frame, 0.007843, (W, H), 127.5)
			net.setInput(blob)
			detections = net.forward()

			# loop over the detections
			for i in np.arange(0, detections.shape[2]):
				# extract the confidence (i.e., probability) associated
				# with the prediction
				confidence = detections[0, 0, i, 2]

				# filter out weak detections by requiring a minimum
				# confidence
				if confidence > 0.5:
					# extract the index of the class label from the
					# detections list
					idx = int(detections[0, 0, i, 1])

					# if the class label is not a person, ignore it
					if CLASSES[idx] != "person":
						continue

					# compute the (x, y)-coordinates of the bounding box
					# for the object
					box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
					(startX, startY, endX, endY) = box.astype("int")

					# construct a dlib rectangle object from the bounding
					# box coordinates and then start the dlib correlation
					# tracker
					tracker = dlib.correlation_tracker()
					rect = dlib.rectangle(startX, startY, endX, endY)
					tracker.start_track(rgb, rect)

					# add the tracker to our list of trackers so we can
					# utilize it during skip frames
					trackers.append(tracker)

		# otherwise, we should utilize our object *trackers* rather than
		# object *detectors* to obtain a higher frame processing throughput
		else:
			# loop over the trackers
			for tracker in trackers:
				# set the status of our system to be 'tracking' rather
				# than 'waiting' or 'detecting'
				status = "Tracking"

				# update the tracker and grab the updated position
				tracker.update(rgb)
				pos = tracker.get_position()

				# unpack the position object
				startX = int(pos.left())
				startY = int(pos.top())
				endX = int(pos.right())
				endY = int(pos.bottom())

				# add the bounding box coordinates to the rectangles list
				rects.append((startX, startY, endX, endY))

		# draw a horizontal line in the center of the frame -- once an
		# object crosses this line we will determine whether they were
		# moving 'up' or 'down'
		W, H = 500, 375
		cv2.line(frame, (0, H // 2), (W, H // 2), (0, 255, 255), 2)

		# use the centroid tracker to associate the (1) old object
		# centroids with (2) the newly computed object centroids
		objects = ct.update(rects)

		# loop over the tracked objects
		for (objectID, centroid) in objects.items():
			# check to see if a trackable object exists for the current
			# object ID
			to = trackableObjects.get(objectID, None)

			# if there is no existing trackable object, create one
			if to is None:
				to = TrackableObject(objectID, centroid)

			# otherwise, there is a trackable object so we can utilize it
			# to determine direction
			else:
				# the difference between the y-coordinate of the *current*
				# centroid and the mean of *previous* centroids will tell
				# us in which direction the object is moving (negative for
				# 'up' and positive for 'down')
				y = [c[1] for c in to.centroids]
				direction = centroid[1] - np.mean(y)
				to.centroids.append(centroid)

				# check to see if the object has been counted or not
				if not to.counted:
					# if the direction is negative (indicating the object
					# is moving up) AND the centroid is above the center
					# line, count the object
					if direction < 0 and centroid[1] < H // 2:
						totalUp += 1
						to.counted = True

					# if the direction is positive (indicating the object
					# is moving down) AND the centroid is below the
					# center line, count the object
					elif direction > 0 and centroid[1] > H // 2:
						totalDown += 1
						to.counted = True

			# store the trackable object in our dictionary
			trackableObjects[objectID] = to

			# draw both the ID of the object and the centroid of the
			# object on the output frame
			text = "ID {}".format(objectID)
			cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
			cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

		# construct a tuple of information we will be displaying on the
		# frame

		now = datetime.now()

		current_time = now.strftime("%H:%M:%S")
		# print("Current Time =", current_time)
		info = [
			("Up", totalUp),
			("Down", totalDown),
			("Status", status),
			("Time", current_time),
		]

		# loop over the info tuples and draw them on our frame
		for (i, (k, v)) in enumerate(info):
			text = "{}: {}".format(k, v)
			cv2.putText(frame, text, (10, H - ((i * 20) + 20)),
				cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)

		# increment the total number of frames processed thus far and
		# then update the FPS counter
		totalFrames += 1
		fps.update()

		print("inside gen: ", info)

		ret, frame = cv2.imencode('.jpeg', frame)

		print("numpy", type(frame))
		# print("got camera frame")
		frame = frame.tobytes()
		print("type:", type(frame))
		# yield (b"--frame\r\n"b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")
		# yield (frame)

def counter(id, stop):
	global i
	gen()
	while True:
		if stop():
			break
		else:
			i = i + 1

def pipe_server(start):
	print("pipe server")
	count = 0
	pipe = win32pipe.CreateNamedPipe(
		r'\\.\pipe\Foo',
		win32pipe.PIPE_ACCESS_DUPLEX,
		win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
		1, 65536, 65536,
		0,
		None)

	print("waiting for client")
	win32pipe.ConnectNamedPipe(pipe, None)
	print("got client")


	stop_threads = False
	if start:
		# t = threading.Thread(target=counter, args=(id, lambda: stop_threads))
		t = threading.Thread(target=gen)
		t.start()

	while True:
		# convert to bytes
		print(type(frame))
		try:

			print(len(frame))
			log.info(len(frame))
			# if frame != []:
			# decoded = cv2.imdecode(np.frombuffer(frame, np.uint8), -1)
			height, width, channels = frame.shape

			print(height,width,channels)

				# cv2.imshow("1.jpg", decoded)
				# cv2.imwrite("images/"+str(count)+"malik.jpg", decoded)
		except:
			print("error")
		# data = str.encode(f"{frame}")
		data = str(frame).encode("utf-8")
		print("DATA: ", len(data))
		# print(str.decode(f"{frame}"))
		# print(f"Sending message", " <- ", count, " -> ", data.decode())
		try:
			win32file.WriteFile(pipe, data)
		except:
			print("finished now")
			# stop_threads = True
			# t.join()
			win32file.CloseHandle(pipe)
			print("pipe break")
			pipe_server(False)
		# time.sleep(1)
		count += 1


if __name__ == '__main__':
	pipe_server(True)