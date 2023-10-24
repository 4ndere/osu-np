import os
import time
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pytz import utc

# Stores script's startup time
start_time = datetime.datetime.utcnow().replace(tzinfo=utc)

# Loads YouTube API Credentials
client_secrets_file = ".json"

# YouTube API V3 Services
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# OAuth Authentication
flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
credentials = flow.run_local_server(port=0)

# Start YouTube API Client with Credentials
youtube = build('youtube', 'v3', credentials=credentials)

# Get Live Chat ID
live_chat_id = ""

# Commands that will trigger the bot
trigger_commands = ["!mapa", "!np", "!song", "!map"]

# Variable to check if a message has been sent
message_sent = False

# Variable to store the ID of sent messages
processed_messages = set()

def get_chat_messages():
    global message_sent
    if message_sent:
        message_sent = False  # Restarts message_sent after sending a message

    request = youtube.liveChatMessages().list(
        liveChatId=live_chat_id,
        part="snippet",
        maxResults=2000
    )
    response = request.execute()

    for item in response['items']:
        # Converts the timestamp of a message into an datetime object
        message_time = datetime.datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%S.%f%z")

        # Verifies if the chat message has any of the commands, also check if it hasnt been proccesed before and if it was sent after the script was initialized
        if any(trigger_command in item['snippet']['displayMessage'] for trigger_command in trigger_commands) and item['id'] not in processed_messages and message_time > start_time:
            print(f"Comando detectado: {item['snippet']['displayMessage']}")  # Prints detected command
            processed_messages.add(item['id'])  # Add the message's ID into proccesed messages
            message_sent = True
            send_message()
            break  # Exits loop after sending a message


def send_message():
    # Reads .txt file, pls make sure it's the correct path :3
    with open('C:\\Program Files (x86)\\StreamCompanion\\Files\\np.txt', 'r') as file:
        message = file.read()

    # Deleted "http://osu.ppy.sh" from the message, YouTube seems to dislike links (or maybe i am just dumb idk)
    message = message.replace("http://osu.ppy.sh", "")

    # Sends the message to live chat.
    request = youtube.liveChatMessages().insert(
        part="snippet",
        body={
            "snippet": {
                "liveChatId": live_chat_id,
                "type": "textMessageEvent",
                "textMessageDetails": {
                    "messageText": message
                }
            }
        }
    )
    response = request.execute()
    print(f"Mensaje enviado: {message}")  # Prints sent message.

# Main loop
while True:
    get_chat_messages()