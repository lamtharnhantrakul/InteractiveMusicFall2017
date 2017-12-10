#from keras.models import load_model
from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from collections import deque
from distutils.util import strtobool
import time
import numpy as np
import threading
#import tensorflow as tf

class data(object):
    def __init__(self, LSTM_lookback=30):
        self.queue = deque()
        self.LSTM_lookback = LSTM_lookback
        self.queue_limit = LSTM_lookback + 10 # give a little budge room
        self.finger_down = False

    def add(self, data_point):
        if len(self.queue) < self.queue_limit:
            self.queue.append(data_point) # add newest value to queue
        else:
            _ = self.queue.popleft() # pop oldest value out of queue
            self.queue.append(data_point) # add newest value to queue
        print(len(self.queue))

    def emptyQueue(self):
        while (len(self.queue) > 0):
            self.queue.popleft()

def data_handler(unused_addr, args, *osc_args):
    dataObj = args[0] # the `data()` object comes through this callback via `args`
    data_point = np.array((osc_args[0],osc_args[1],osc_args[2])) # any OSC data routed through address `/light_pad
    dataObj.add(data_point)

def finger_touch_handler(unused_addr, args, finger_down_bool):
    dataObj = args[0]
    dataObj.emptyQueue()  # empty the queue when user touches lightpad or when they release their finger
    dataObj.finger_down = strtobool(finger_down_bool)

if __name__ == '__main__':
    # Define an object that holds all data that is sent from Max/MSP
    MaxData = data()

    # Define the server -> Max/MSP port
    maxClient = udp_client.UDPClient('127.0.0.1', 8000)

    # Define the server_thread
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/lightpad_data", data_handler, MaxData)
    dispatcher.map("/finger_down", finger_touch_handler, MaxData)

    server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 8001), dispatcher)
    serverThread = threading.Thread(target=server.serve_forever)

    # Define the prediction_thread
    #stateThread = stateMachineThread(MaxData)

    # Start the two threads
    serverThread.start()
