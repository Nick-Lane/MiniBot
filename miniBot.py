import discord
from datetime import datetime, timedelta, date
import re
import random



class Result:
    def __init__(self, date: datetime.date, time: int):
        self.date = date
        self.time = time
    def __str__(self):
        return f"Date:{self.date}, time: {self.time}"


class Preference:
    def __init__(self,type: str, value: int):
        self.type = type
        self.value = value

class MbUser:
    def __init__(self, id: discord.user):
        self.id = id # id is a discord user
        self.results = [] # list of type Result
        self.preferences = [] # list of type Preference
        self.times_placed = [] # number of times placed 1st, 2nd, etc. index 0 will be empty so index 1 is 1st, etc.

    def add(self, res: Result, chn: discord.channel):
        self.results.append(res)
        for i in self.results:
            if i.date < date.today():
                self.results.remove(i)
        self.congratulate(chn)

    def get_preference(self, pref_type: str) -> Preference:
        for p in self.preferences:
            if p.type == pref_type:
                return True
        return False
    
    def congratulate(self, chnl: discord.channel):
        file_name = "files/congratsMessages"
        # if the player has specified a ratio for how often they want to see goofy congratulation messages
        if self.has_preference("goofy_ratio"):
            # if they roll more than their ratio, they get a normal message.
            # if they roll less than or equal to their ratio, they get a goofy one. IDK, this made sense when I wrote it
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
    
    def get_todays_result(self) -> Result | None:
        for r in self.results:
            if r.date == date.today():
                return r
        return None


class Placing:
    def __init__(self, user: MbUser, result: Result):
        self.user = user
        self.result = result
        self.place = -1



class Permissions:
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
    
    # accepts a string, str, which is the Preference we're asking for
    # returns a list of strings, which are the usernames of users with that Preference or None
    def get(self, str):
        for i in self.p:
            print(i)
            if i.startswith(str):
                return i[len(str)+1:].split()
        return None



class MiniBot:
    def __init__(self):
        self.users = [] # list of type MbUser
        self.per = Permissions("files/Permissions")
    
    def is_user(self, userID):
        for u in self.users:
            if u.id == userID:
                return True
        return False
    
    def get_mb_user(self, userID: discord.user) -> MbUser:
        for u in self.users:
            if u.id == userID:
                return u
        return None
    
    # add a Result to the user that submitted it
    def add(self, res: Result, mes: discord.message):
        # if the submitter isn't already in the system
        userID = mes.author
        if not self.is_user(userID):
            self.users.append(MbUser(userID))

        # add the results to the user's results
        self.get_mb_user(userID).add(res, mes.channel) 

        
    
    # Function to return Result object, if the message is a mini Result
    def check_result(self, message_content) -> Result | None:
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

        # create a Result object and return it
        return Result(date,time)
    
    def feed(self, message: discord.message):
        r = self.check_result(message.content)

        # if it's a Result
        if r is not None:
            self.add(r, message)
        # TODO implement commands
    
    def daily_leaderboard(self, channel: discord.channel):
        message = "DAILY LEADERBOARD:\n"
        placings = []
        unsorted_placings = []
        for u in self.users:
            r = u.get_todays_result()
            if r is not None:
                unsorted_placings.append(Placing(u,r))
        if (len(unsorted_placings) > 0):
            placings = sorted(unsorted_placings, key = lambda x: x.result.time)
            placings.insert(0,"zero")
            i = 1
            while (i < len(placings)):
                message += f"{i}. {placings[i].user.id.display_name} {placings[i].result.time}\n"
                placings[i].user.place(i)
                i += 1


            




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