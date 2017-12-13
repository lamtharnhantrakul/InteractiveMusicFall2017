from keras.models import load_model
from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from collections import deque
import time
import numpy as np
import threading
import tensorflow as tf

# Load a trained model
graph = tf.get_default_graph() # hack around keras tensorflow in multiple threads
# read https://github.com/fchollet/keras/issues/5896 for more information on the hack
print("loading model...")
with graph.as_default():
    model = load_model('./models/test_model_30.h5')
print("completed model...")


# Define the server -> Max/MSP port
maxClient = udp_client.UDPClient('127.0.0.1', 8000)
print("Max/MSP to Server connection Initiated")

# Define a buffer of values that the UDP server_thread will write to
queue = deque()
queue_limit = 40  # same number as LSTM lookback
LSTM_lookback = 30



# rewrite according to https://github.com/AvneeshSarwate/MUS7100_Fall_2017/blob/master/Interface-5/LemurBounce2.pyçç
def sendUDPmsg(index,prediction):
    msg = osc_message_builder.OscMessageBuilder(address = '/prediction')
    msg.add_arg(int(index)) # prepend with an index for Max/MSP `coll` object
    msg.add_arg(float(prediction[0])) # x coor
    msg.add_arg(float(prediction[1])) # y coor
    msg.add_arg(float(prediction[2])) # pressure
    msg = msg.build()
    maxClient.send(msg)

def sendUDPcommand(command_type, command_idx):
    msg = osc_message_builder.OscMessageBuilder(address = command_type)
    msg.add_arg(int(command_idx))
    msg = msg.build()
    maxClient.send(msg)

def genSendPredictions(init_sequence):
    pattern = np.array(init_sequence)

    start_time = time.time()
    with graph.as_default():
        for i in range(100):
            x = np.reshape(pattern, (1, pattern.shape[0], pattern.shape[1]))
            prediction = model.predict(x, verbose=0)
            #print(prediction.shape)
            prediction_reshaped = np.squeeze(prediction)
            sendUDPmsg(i, prediction_reshaped)  # Send message via UDP immediatly as it is generated
            pattern = np.concatenate((pattern, prediction), axis=0)
            pattern = pattern[1:len(pattern),:]

        final_x = prediction_reshaped[0]
        final_y = prediction_reshaped[1]
        final_pressure = prediction_reshaped[2]
        fade_pressures = np.linspace(final_pressure, 0.0, num=20)

        for j in range(20):
            ramp_values = np.array((final_x, final_y, fade_pressures[j]))
            sendUDPmsg(j+100, ramp_values)


    #print("--- %s seconds ---" % (time.time() - start_time))

def data_handler(unused_addr,x_coor,y_coor,pressure):
    data_point = np.array((x_coor,y_coor,pressure))
    if len(queue) < queue_limit:
        queue.append(data_point)
    else:
        _ = queue.popleft() # pop oldest value out of queue
        queue.append(data_point) # add newest value to queue
    print(len(queue))

def finger_touch_handler(unused_addr, touch_idx):
    # empty the queue when user touches lightpad or when they release their finger
    while (len(queue) > 0):
        queue.popleft()

class predictionThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.init_sequence = []
        self.state = 'listening_state'

    def run(self):
        # This thread is a finite state machine
        while True:
            if self.state == 'listening_state':
                if len(queue) > LSTM_lookback:
                    while len(self.init_sequence) < LSTM_lookback: # LSTM_lookback = 30
                        self.init_sequence.append(queue.popleft())
                    print(len(queue))

                    self.state = 'predicting_state'

            elif self.state == 'predicting_state':
                genSendPredictions(self.init_sequence)
                sendUDPcommand("/player",1)
                self.init_sequence = []
                self.state = 'listening_state'

if __name__ == '__main__':

    # Define the server_thread
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/data", data_handler)
    dispatcher.map("/finger_touch", finger_touch_handler)

    server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 8001), dispatcher)
    server_thread = threading.Thread(target=server.serve_forever)
    print("Server to Max/MSP Client initiated")

    # Define the prediction_thread
    prediction_thread = predictionThread()

    # Start the two threads
    server_thread.start()
    prediction_thread.start()
    print("Exiting main thread")
