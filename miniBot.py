import discord
from datetime import datetime, timedelta, date
import re
import random



class result:
    def __init__(self, date: datetime.date, time: int):
        self.date = date
        self.time = time
    def __str__(self):
        return f"Date:{self.date}, time: {self.time}"

class preference:
    def __init__(self,type: str, value: int):
        self.type = type
        self.value = value

class mb_user:
    def __init__(self, id: discord.user):
        self.id = id # id is a discord user
        self.results = [] # list of type result
        self.preferences = [] # list of type preference
        self.times_placed = [] # number of times placed 1st, 2nd, etc. index 0 will be empty so index 1 is 1st, etc.

    def add(self, res: result, chn: discord.channel):
        self.results.append(res)
        for i in self.results:
            if i.date < date.today():
                self.results.remove(i)
        self.congratulate(chn)

    def has_preference(self, pref_type: str) -> bool:
        for p in self.preferences:
            if p.type == pref_type:
                return True
        return False
    
    def congratulate(self, chnl: discord.channel):
        file_name = "files/congratsMessages"
        # if the player has specified a ratio for how often they want to see goofy congratulation messages
        if hasattr(self, "goofy_ratio"):
            # if they roll more than their ratio, they get a normal message.
            # if they roll less than their ratio, they get a goofy one. IDK, this made sense when I wrote it
            if random.randRange(1,10) <= self.goofy_ratio:
                file_name = "files/goofyCongratsMessages"
        file = open(file_name, "r")
        congrats_messages = file.readlines()
        file.close()
        # send a random congratulation message from the appropriate list to the appropriate channel
        chnl.send(congrats_messages[random.randrange(0,len(congrats_messages))])
    
    def place(self, pl):
        # if the list isn't long enough to accept the place given, extend it the proper length
        if pl >= len(self.times_placed):
            self.times_placed += [0] * (pl - len(self.times_placed) +1)
        self.times_placed[pl] += 1





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



class MiniBot:
    def __init__(self):
        self.users = [] # list of type mb_user
        self.per = permissions("files/permissions")
    
    def is_user(self, userID):
        for u in self.users:
            if u.id == userID:
                return True
        return False
    
    def get_mb_user(self, userID: discord.user) -> mb_user:
        for u in self.users:
            if u.id == userID:
                return u
        return None
    
    # add a result to the user that submitted it
    def add(self, res: result, mes: discord.message):
        # if the submitter isn't already in the system
        userID = mes.author
        if not self.is_user(userID):
            self.users.append(mb_user(userID))

        # add the results to the user's results
        self.get_mb_user(userID).add(res, mes.channel) 

        
    
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
            self.add(r, message)
            




# global object
bot = MiniBot() #TODO change so it starts as none, then in on_ready, initialize so it can read in JSON and remember everyone's info

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