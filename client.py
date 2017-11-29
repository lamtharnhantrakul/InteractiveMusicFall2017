# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import socket
# END IMPORTS

# Instantiates a client
client = language.LanguageServiceClient()

# Sets up a UDP port for communication with MaxMSP

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

while True:
    print('-' * 70)
    text = input("Enter text to analyze: ")
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment

    #print('Text: {}'.format(text))
    print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))

    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
    sock.sendto(bytes(text, "utf-8"), (UDP_IP, UDP_PORT))
    print('Message sent through UDP:',UDP_IP,UDP_PORT)
