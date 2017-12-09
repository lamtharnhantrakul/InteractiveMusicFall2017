ok
upyter notebo# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import socket
from pythonosc import osc_message_builder
from pythonosc import udp_client
# END IMPORTS

# Instantiates a client
client = language.LanguageServiceClient()

# Sets up a UDP port for communication with MaxMSP
maxClient = udp_client.UDPClient('127.0.0.1', 8000)

def sendUDPmsg(score, magnitude):
    msg = osc_message_builder.OscMessageBuilder(address = '/sentiment')
    msg.add_arg(score)
    msg.add_arg(magnitude)
    msg = msg.build()
    maxClient.send(msg)
    print('Message sent through UDP:','127.0.0.1',8000)

# Send an init message
sendUDPmsg(0.0, 1.0)

# Loop
while True:
    print('-' * 70)
    text = input("Enter text to analyze: ")
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment
    print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))

    # Packages message to send to Max/MSP via UDP
    sendUDPmsg(sentiment.score,sentiment.magnitude)
