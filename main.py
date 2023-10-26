import os
import time
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pytz import utc

# Stores script's startup time
start_time = datetime.datetime.utcnow().replace(tzinfo=utc)

# Loads YouTube API Credentials .json
client_secrets_file = ".json"

# YouTube API V3 Services
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# OAuth Authentication
flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
credentials = flow.run_local_server(port=0)

# Start YouTube API Client with Credentials
youtube = build('youtube', 'v3', credentials=credentials)

# Get Live Chat ID
def get_live_chat_id():
    request = youtube.liveBroadcasts().list(
        part="snippet",
        broadcastType="all",
        mine=True,
        maxResults=1
    )
    response = request.execute()

    if 'items' in response and len(response['items']) > 0:
        return response['items'][0]['snippet']['liveChatId']
    else:
        return None

live_chat_id = get_live_chat_id()

# Gets active Live Chat ID every 30 seconds, loops stops if a livestream is found
while live_chat_id is None:
    print("No livestream found, retrying in 30s...")
    time.sleep(30)
    live_chat_id = get_live_chat_id()

print("Livestream Found, Live Chat ID: ", live_chat_id)

# Commands that will trigger the bot
trigger_commands = ["!np", "!map"]

# Variable to check if a message has been sent
message_sent = False

# Variable to store the ID of sent messages
processed_messages = set()

# Variable to store the last time a command was processed
last_command_time = 0

def get_chat_messages():
    global message_sent, last_command_time, command_found
    if message_sent:
        message_sent = False  # Restarts message_sent after sending a message

    request = youtube.liveChatMessages().list(
        liveChatId=live_chat_id,
        part="snippet",
        maxResults=10
    )

    response = request.execute()
    command_found = False

    for item in response['items']:
        # Converts the timestamp of a message into an datetime object
        message_time = datetime.datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%S.%f%z")

        # Verifies if the chat message is exactly one of the commands, also check if it hasn't been processed before and if it was sent after the script was initialized
        if item['snippet']['displayMessage'] in trigger_commands and item['id'] not in processed_messages and message_time > start_time:
            # Check if at least 10 seconds have passed since the last command
            current_time = time.time()
            if current_time - last_command_time < 5:
                return

            print(f"Command detected: {item['snippet']['displayMessage']}")  # Prints detected command
            processed_messages.add(item['id'])  # Add the message's ID into processed messages
            last_command_time = current_time  # Update the last command time
            message_sent = True
            send_message()
            command_found = True
            break  # Exits loop after sending a message

    return command_found


def send_message():
    # Reads .txt file, pls make sure it's the correct path !!!
    with open('C:\\Program Files (x86)\\StreamCompanion\\Files\\np.txt', 'r') as file:
        message = file.read()

    # Deletes "http://osu.ppy.sh" from the message, YouTube seems to dislike links
    message = message.replace("http://osu.ppy.sh", "")
    # This works for unsubmitted maps, it replaces the link for the desired text
    message = message.replace("/s/-1","Map not Uploaded!")


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

    # Console output for sent messages
    print(f"Message sent: {message}")  

# Main loop
while True:
    get_chat_messages()
    start_time = datetime.datetime.utcnow().replace(tzinfo=utc)
    if command_found:
     time.sleep(5)  # Cooldown for 5 seconds only if a command was found