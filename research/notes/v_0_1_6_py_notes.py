
# Calibration.py
# --------------

# the parser process queue self._parser6 handle the errors and loop counter

# self._flag  	= Boolean variable to process exceptions
# self._flag2 	= Boolean variable to process exceptions
# self._flag2 	= Boolean variable to process exceptions
# k 			= calibration loop counter
# None			= none
# None			= none

# init the parser process queue self._parser6
self._parser6 = parser_process

# add variable to the parser process queue named self._parser6
self._parser6.add6([
	self._flag, 
	self._flag2, 
	self._flag2, 
	k, 
	None, 
	None
	])


# Parser.py
# --------------
# init parser queue
self._out_queue6 = data_queue6

# add data to queue 
def add6(self, data):
	self._out_queue6.put(data) 

# worker.py
# --------------
# start the parser process in worker 
self._parser_process = ParserProcess(
	self._queue1, 
	self._queue2, 
	self._queue3, 
	self._queue4, 
	self._queue5, 
	self._queueCurrentTec, 
	self._queue6, 
	self._queue_F_multi, 
	self._queue_D_multi, 
	self._queue_A_multi, 
	self._queue_P_multi
	)

# init queue
self._queue6 = Queue()

# method define the queue
def _queue_data6(self,data):
	#:param data: values to add for serial error :type data: float.
	self._ser_error1 = data[0]
	self._ser_error2 = data[1]
	self._control_k = data[2]
	self._ser_err_usb = data[3]
	self._overtone_number = data[4]
     
    # VER 0.2 
    # get TEC status 
    self._TEC_status = data[5]

# method consume queue6 
def consume_queue6(self):
	# queue3 for elaborated data: errors
	while not self._queue6.empty():
		self._queue_data6(self._queue6.get(False))

# method get serial error
def get_ser_error(self):
	return self._ser_error1, self._ser_error2, self._control_k, self._ser_err_usb, self._overtone_number

# mainWindow.py 
# --------------

# update plot method 
def _update_plot(self):
	# consume the error queue 
    self.worker.consume_queue6()

# call the worker method get_ser_error and get error values 
error1, error2, error3, self._ser_control, self._overtone_number = self.worker.get_ser_error()




