import logging

class CustomAdapter(logging.LoggerAdapter):
	"""
	This example adapter expects the passed in dict-like object to have a
	'connid' key, whose value in brackets is prepended to the log message.
	"""
	def process(self, msg, kwargs):
		return '[%s] %s' % (self.extra['connid'], msg), kwargs

def createLogs(filename):
	file_h = logging.FileHandler(filename+".log", "a+")
	formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
	file_h.setFormatter(formatter)

	logger = logging.getLogger()

	for hdlr in logger.handlers[:]:
		logger.removeHandler(hdlr)

	logger.addHandler(file_h)

	logger.setLevel(logging.DEBUG) 

	logger = CustomAdapter(logger, {'connid': "research"})

	return logger

# logs = createLogs("research.txt")

# logs.info("-=-=-=-=-=-==-=-=-==-") 

# logs.debug("Harmless debug Message") 
# logs.info("Just an information") 
# logs.warning("Its a Warning") 
# logs.error("Did you try to divide by zero") 
# logs.critical("Internet is down")