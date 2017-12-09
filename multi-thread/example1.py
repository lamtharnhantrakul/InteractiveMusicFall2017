import threading
import time

# Define a function for the thread
def print_time( threadName, delay):
    count = 0
    while count < 0:
        time.sleep(delay)
        count += 1
        print ("%s: %s" % ( threadName, time.ctime(time.time()) ))

# Create two new threads as follows
try:
    threading.start_new_thread( print_time, ("thread-1", 2, ) )
    threading.start_new_thread( print_time, ("thread-2", 4, ) )
except:
    print("Error: unable to start thread")

while 1:
    pass
