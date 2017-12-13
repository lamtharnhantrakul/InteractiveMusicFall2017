import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
#MESSAGE = "Hello, World!"

while True:
    print('-' * 70)
    MESSAGE = input("Message you'd like to send: ")
    print ("UDP target IP:", UDP_IP)
    print ("UDP target port:", UDP_PORT)
    print ("message:", MESSAGE)

    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    sock.sendto(bytes(MESSAGE, "utf-8"), (UDP_IP, UDP_PORT))
