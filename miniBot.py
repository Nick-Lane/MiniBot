import discord
from datetime import datetime, timedelta
import re



class result:
    def __init__(self, date: datetime.date, time: int):
        self.date = date
        self.time = time
    def __str__(self):
        return f"Date:{self.date}, time: {self.time}"

class mb_user:
    def __init__(self, id: discord.user):
        self.id = id # id is a discord user
        self.results = [] # list of type result

class permissions:
    def __init__(self,fname: str):
        self.p = []
        file = open(fname, "r")
        self.p = file.readlines()
        file.close()
    
    # accepts a string, str, which is the permission we're asking for
    # returns a list of strings, which are the usernames of users with that permission, or None
    def get(self, str):
        for i in self.p:
            print(i)
            if i.startswith(str):
                return i[len(str)+1:].split()
        return None

class preferences:
    def __init__(self,fname: str):
        self.p = []
        file = open(fname, "r")
        self.p = file.readlines()
        file.close()
    
    # accepts a string, str, which is the preference we're asking for
    # returns a list of strings, which are the usernames of users with that preference or None
    def get(self, str):
        for i in self.p:
            print(i)
            if i.startswith(str):
                return i[len(str)+1:].split()
        return None

class mini_bot:
    def __init__(self):
        self.users = [] # list of type mb_user
        self.per = permissions("files/permissions")
        self.pref = preferences("files/preferences")
    
    def is_user(self, userID):
        for u in self.users:
            if u.id == userID:
                return True
        return False
    
    def get_mb_user(self, userID: discord.user):
        for u in self.users:
            if u.id == userID:
                return u
        return None
    
    # add a result to the user that submitted it
    def add(self, res: result, userID: discord.user):
        # if the submitter isn't already in the system
        if not self.is_user(userID):
            self.users.append(mb_user(userID))
        

        
    
    # Function to return result object, if the message is a mini result
    def check_result(self, message_content):
        # regular expressions to match the patterns
        url_pattern = r"https://www.nytimes.com/badges/games/mini.html\?d=(\d{4}-\d{2}-\d{2})&t=(\d+)"
        app_pattern = r"I solved the (\d{1,2}/\d{1,2}/\d{4}) New York Times Mini Crossword in (\d{1,2}):(\d{2})"

        # match the patterns
        url_match = re.match(url_pattern, message_content)
        app_match = re.match(app_pattern, message_content)

        if url_match:
            date_str = url_match.group(1)
            date_format = "%Y-%m-%d"
            time = int(url_match.group(2))
        elif app_match:
            date_str = app_match.group(1)
            date_format = "%m/%d/%Y"
            minutes = int(app_match.group(2))
            seconds = int(app_match.group(3))
            time = minutes * 60 + seconds # convert minutes and seconds to seconds
        else:
            return None

        # convert the date string to a datetime.date object
        date = datetime.strptime(date_str, date_format).date()

        # create a result object and return it
        return result(date,time)
    
    def feed(self, message: discord.message):
        r = self.check_result(message.content)

        # if it's a result
        if r:
            self.add(r, message.author)



# global object
bot = mini_bot() 

class myClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {client.user}")

    async def on_message(self, message):
        # Don't respond to your own message
        if message.author == client.user:
            return
        
        # send the message to the bot 
        bot.feed(message)
    
    
    
    






# initialize the Discord client
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = myClient(intents=intents)

# bot's token
token_file = open("files/token", "r")
token = token_file.read()
token_file.close()



# Run the bot
client.run(token)