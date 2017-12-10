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
from distutils.util import strtobool
#import tensorflow as tf

vals = {}
vals['player_state'] = 0

def data_handler(unused_addr, args, *osc_args):
    # (args[0], args[1] = (queue, queue_limit)
    # (osc_args[0],osc_args[1],osc_args[2]) = (x_coor, y_coor, pressure)
    queue = args[0]
    queue_limit = args[1]

    data_point = np.array((osc_args[0],osc_args[1],osc_args[2]))
    if len(queue) < queue_limit:
        queue.append(data_point)
    else:
        _ = queue.popleft() # pop oldest value out of queue
        queue.append(data_point) # add newest value to queue
    print(len(queue))

def finger_touch_handler(unused_addr, args, *osc_args):
    # (args[0], args[1] = (queue, finger_down)
    # osc_args[0] = finger_down (true or false) from Max/MSP

    # Change the state of finger_down
    finger_down = args[1]
    finger_down = int(osc_args[0])
    #print("finger_down:",finger_down)
    # empty the queue when user touches lightpad or when they release their finger
    queue = args[0]
    while (len(queue) > 0):
        queue.popleft()

def player_state_handler(unused_addr, args, *osc_args):
    # args[0] = player_state
    # osc_args[0] = player_state (0 or 1) from Max/MSP

    # Change the state of plater_state
    player_state = args[0]
    plater_state = int(osc_args[0])
    print ("player_state:", player_state)

def sendUDPmsg(address,maxClient,*args):
    msg = osc_message_builder.OscMessageBuilder(address = address)
    for arg in args:
        msg.add_arg(arg)
    msg = msg.build()
    maxClient.send(msg)

if __name__ == '__main__':
    # Define the data that will be manipulated by the handlers
    queue = deque()
    queue_limit = 40
    LSTM_lookback = 30
    finger_down = 0
    player_state = 0

    # Define the server -> Max/MSP port
    maxClient = udp_client.UDPClient('127.0.0.1', 8000)

    # Define the server_thread
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/lightpad_data", data_handler, queue, queue_limit)
    dispatcher.map("/finger_down", finger_touch_handler, queue, finger_down)
    dispatcher.map("/player_state", player_state_handler, player_state)

    server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 8001), dispatcher)
    serverThread = threading.Thread(target=server.serve_forever)

    # Start the server threads
    serverThread.start()

    # Define data needed for the finite state machine
    state = 'listening'
    init_seq = []

    while True:
        #print(self.state)
        print("player_state:", player_state)
        if state == 'listening':
            if len(queue) >= LSTM_lookback:
                while len(init_seq) < LSTM_lookback: # LSTM_lookback = 30
                    init_seq.append(queue.popleft())
                state = 'predicting'
                print("switched to predicting state")

        elif state == 'predicting':

            # predict
            init_seq = []  # clear the init_seq

            player_state = 1
            sendUDPmsg("/player_state", maxClient, int(player_state))
            state = 'playing'
            print("switched to playing state")

        elif state == 'playing':

            if player_state == 0:
                # The Max Player finished playing, so go back to listening
                state = 'listening'
                print("switched to listening state")
            elif len(queue) > 15 and player_state == 1:
                # This must be an interruption
                print("Interrupted!")
                player_state = 0
                sendUDPmsg("/player_state", maxClient, int(player_state))
                state = 'listening'
                print("switched to listening state")
