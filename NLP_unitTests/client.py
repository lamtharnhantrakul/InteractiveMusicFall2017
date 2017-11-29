# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

# Instantiates a client
client = language.LanguageServiceClient()

# The text to analyze
try:
    while True:
        text = input("Enter text to analyze: ")
        #text = u'I loves you, world!'
        document = types.Document(
            content=text,
            type=enums.Document.Type.PLAIN_TEXT)

        # Detects the sentiment of the text
        sentiment = client.analyze_sentiment(document=document).document_sentiment

        print('Text: {}'.format(text))
        print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))
except (KeyboardInterrupt, SystemExit):
    raise
