import discord
from datetime import datetime, timedelta
import re

# initialize the Discord client
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

# bot's token
token_file = open("token", "r")
token = token_file.read()

class result:
    def __init__(self, date, time: int):
        self.date = date
        self.time = time

class mb_user:
    def __init__(self, id: discord.user):
        self.id = id # id is a discord user

class mb_users:
    def __init__(self):
        self.users = [] # list of type mb_user
    
    def is_user(self, userID):
        for u in users:
            if u.id == userID:
                return True
        return False

# global object
users = mb_users() 

# Function to return result object, if the message is a mini result
def check_result(message):
    # regular expressions to match the patterns
    url_pattern = r"https://www.nytimes.com/badges/games/mini.html\?d=(\d{4}-\d{2}-\d{2})&t=(\d+)"
    app_pattern = r"I solved the (\d{1,2}/\d{1,2}/\d{4}) Mini Crossword in (\d{1,2}):(\d{2})"

    # match the patterns
    url_match = re.match(url_pattern, message)
    solved_match = re.match(app_pattern, message)

    if url_match:
        date_str = url_match.group(1)
        date_format = "%Y-%m-%d"
        time = int(url_match.group(2))
    elif solved_match:
        date_str = solved_match.group(1)
        date_format = "%m/%d/%Y"
        minutes = int(solved_match.group(2))
        seconds = int(solved_match.group(3))
        time = minutes * 60 + seconds # convert minutes and seconds to seconds
    else:
        return None

    # convert the date string to a datetime object
    date = datetime.strptime(date_str, date_format).date()

    # create a result object and return it
    return result(date,time)

# Event: when the bot is ready
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

# Event: when a message is received
@client.event
async def on_message(message):
    # Don't respond to your own message
    if message.author == client.user:
        return
    
    r = check_result(message.content)

    if r: # if it's a result post
        if not users.is_user(message.author): # if it's a result post and they're not in the system yet
            users.add(mb_user(message.author))
    
    # TODO implement commands

# Run the bot
client.run(token)