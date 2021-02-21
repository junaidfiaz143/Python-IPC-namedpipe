from multiprocessing.connection import Listener
import cv2

address = ("localhost", 6000)     # family is deduced to be 'AF_INET'
listener = Listener(address, authkey=b"secret_password")
conn = listener.accept()
print ("connection accepted from", listener.last_accepted)

while True:
	try:
		msg = ""
		msg = conn.recv()
		print(type(msg))
		# cv2.imshow("frame", msg)
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()
		msg = "ok"
	except:
		pass

	if msg != "" and msg != "close":
		print(msg)
		conn = listener.accept()
	else:
		conn.close()
		break

listener.close()