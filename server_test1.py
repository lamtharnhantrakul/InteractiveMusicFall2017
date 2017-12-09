#from keras.models import load_model
from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
from collections import deque
import numpy as np
import threading

'''
# Load a trained model
print("loading model...")
model = load_model('./models/test_model_30.h5')
print("completed model...")
'''

# Define the server -> Max/MSP port
maxClient = udp_client.UDPClient('127.0.0.1', 8000)
print("Max/MSP to Server connection Initiated")

# Define a buffer of values that the UDP thread will write to
queue = deque()
queue_limit = 40  # same number as LSTM lookback
LSTM_lookback = 30

def sendUDPmsg(index,prediction):
    msg = osc_message_builder.OscMessageBuilder(address = '/prediction')
    msg.add_arg(int(index)) # prepend with an index for Max/MSP `coll` object
    msg.add_arg(float(prediction[0])) # x coor
    msg.add_arg(float(prediction[1])) # y coor
    msg.add_arg(float(prediction[2])) # pressure
    msg = msg.build()
    maxClient.send(msg)

'''
def genSendPredictions(init_sequence):
    pattern = init_sequence
    #sequence = []
    start_time = time.time()
    for i in range(100):
        x = np.reshape(pattern, (1, pattern.shape[0], pattern.shape[1]))
        prediction = model.predict(x, verbose=0)
        prediction_reshaped = np.squeeze(prediction)
        sendUDPmsg(i, prediction_reshaped)  # Send message via UDP immediatly as it is generated
        #sequence.append(prediction_reshaped)
        pattern = np.concatenate((pattern, prediction), axis=0)
        pattern = pattern[1:len(pattern),:]
    #sequence = np.asarray(sequence)

    print("--- %s seconds ---" % (time.time() - start_time))

'''

def data_handler(unused_addr,idx,x_coor,y_coor,pressure):
    data_point = np.array((x_coor,y_coor,pressure))
    if len(queue) < queue_limit:
        queue.append(data_point)
    else:
        _ = queue.popleft() # pop oldest value out of queue
        queue.append(data_point) # add newest value to queue
    print(len(queue))

if __name__ == '__main__':
    state = 'listening'

    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/data", data_handler)

    server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 8001), dispatcher)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    print("Server to Max/MSP Client initiated")

    print("Ready to run...")

    # main loop is a finite state machine
    while True:
        if state == 'listening':
            init_sequence = []
            if len(queue) > LSTM_lookback:
                while len(init_sequence) < LSTM_lookback: # LSTM_lookback = 30
                    init_sequence.append(queue.popleft())
                state == 'predicting'
            else:
                print("queue does not contain enough initial values")
        elif state == 'predicting':
            print('predicting!')
