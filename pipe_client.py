import time
import win32pipe, win32file, pywintypes
import sys
import numpy as np
np.set_printoptions(threshold=sys.maxsize)
import cv2
import ast
import logs

import json

log = logs.createLogs("client")

global count
count = 0

def pipe_client():
	print("pipe client")
	quit = False

	global count

	while not quit:
		try:
			handle = win32file.CreateFile(
				r'\\.\pipe\Foo',
				win32file.GENERIC_READ | win32file.GENERIC_WRITE,
				0,
				None,
				win32file.OPEN_EXISTING,
				0,
				None
			)
			res = win32pipe.SetNamedPipeHandleState(handle, win32pipe.PIPE_READMODE_MESSAGE, None, None)
			if res == 0:
				print(f"SetNamedPipeHandleState return code: {res}")
			while True:
				# resp = win32file.ReadFile(handle, 64*1024)
				resp = win32file.ReadFile(handle, 500*375*3)



				# print("Received message ", resp[1])
				# print(type(resp[1]))
				# print(type(resp[1].decode("utf-8")))
				try:
					# decoded = cv2.imdecode(np.frombuffer(resp[1].decode("utf-8").tobytes(), np.uint8), -1)
					# h, w, c = decoded.shape

					# print(h, w, c)

					# np_image = np.fromstring(resp[1].decode("utf-8"), np.int8)
					# print(np_image)

					# image = cv2.resize(np_image, (500, 375))

					count = count + 1

					# decoded = cv2.imdecode(np.frombuffer(resp[1], np.uint8), -1)
					# print(decoded)
					# print(resp[1].decode("utf-8").encode())
					# cv2.imwrite("images/"+str(count)+"malik.jpg", resp[1].decode("utf-8").encode())
				except Exception as e:
					print(str(e))
				# print(type(resp[1].decode("utf-8")))
				try:
					i = resp[1].decode("utf-8").replace("\n", "")
					i = i.replace("  ", ",")
					i = i.replace(" ", ",")
					i = i.replace("[,", "")
					# x = ast.literal_eval(i)
					# x = json.loads(i)
					print(i)
					log.info(i)				
					f = open("img.txt", "a+")
					f.write(i)
					f.close()
					print(type(i))
				except Exception as e:
					print(e)
				# print(list(resp[1].decode("utf-8")))
				# print(type(list(resp[1].decode("utf-8"))))
		except pywintypes.error as e:
			if e.args[0] == 2:
				print("no pipe, trying again in a sec")
				time.sleep(1)
			elif e.args[0] == 109:
				print("broken pipe, bye bye")
				quit = True


if __name__ == '__main__':
	pipe_client()