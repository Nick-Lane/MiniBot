import discord
from datetime import datetime, timedelta, date
import re
import random



class Result:
    def __init__(self, date: datetime.date, time: int):
        self.date = date
        self.time = time
    def __str__(self):
        return f'Date:{self.date}, time: {self.time}'

# preference types:
# no_congrats
# no_rekkening
# no_leaderboard
# goofy_ratio
class Preference:
    def __init__(self, type: str, value: int):
        self.type = type
        self.value = value

# Command class. 
        # type: 'user' | 'admin' 
        # content: just the command (no 'minibot' or 'mb')
        # user: the discord User executing the command.
        # message: discord Message in which the command was sent
class Command:
    def __init__(self, type: str, content: str, user: discord.User, message: discord.Message):
        self.type = type
        self.content = content
        self.user = user
        self.message = message

class MbUser:
    def __init__(self, id: discord.user):
        self.id = id # id is a discord user
        self.results = [] # list of type Result
        self.preferences = [] # list of type Preference
        self.times_placed = [] # number of times placed 1st, 2nd, etc. index 0 will be empty so index 1 is 1st, etc.

    async def add(self, res: Result, chn: discord.TextChannel):
        self.results.append(res)
        for i in self.results:
            if i.date < date.today():
                self.results.remove(i)
        if res.date > date.today:# if it's tomorrow's puzzle
            await chn.send(f'Great job on tomorrow\'s puzzle, {self.id.displayName}!')
            return
        await self.congratulate(chn)

    def get_preference(self, pref_type: str) -> Preference:
        for p in self.preferences:
            if p.type == pref_type:
                return p
        return None
    
    def clear_preference(self, pref_type: str):
        self.preferences = [pref for pref in self.preferences if pref.type != pref_type]

    def set_preference(self, preference: Preference):
        if preference.type.startswith('yes'):
            self.clear_preference('no' + preference.type[3:])
            return
        if preference.type == 'goofy_ratio':
            if preference.value > 10:
                preference.value = 10
            if preference.value < 0:
                preference.value = 0
            if preference.value == 0:
                self.clear_preference('goofy_ratio')
                return
        # if they already have the preference, remove it
        self.clear_preference(preference.type)
        self.preferences.add(preference)

    async def congratulate(self, chnl: discord.TextChannel):
        if self.get_preference('no_congrats'):
            return
        file_name = 'files/congratsMessages'
        # if the player has specified a ratio for how often they want to see goofy congratulation messages
        if self.get_preference('goofy_ratio'):
            # if they roll more than their ratio, they get a normal message.
            # if they roll less than or equal to their ratio, they get a goofy one. IDK, this made sense when I wrote it
            if random.randRange(1,11) <= self.get_preference('goofy_ratio').value:
                file_name = 'files/goofyCongratsMessages'
        file = open(file_name, 'r')
        congrats_messages = file.readlines()
        file.close()
        # send a random congratulation message from the appropriate list to the appropriate channel
        message = congrats_messages[random.randrange(0,len(congrats_messages))]
        message = message.replace('uname', self.id.displayName)
        await chnl.send(message)
    
    def place(self, pl):
        # if the list isn't long enough to accept the place given, extend it the proper length
        if pl >= len(self.times_placed):
            self.times_placed += [0] * (pl - len(self.times_placed) +1)
        self.times_placed[pl] += 1
    
    def get_todays_result(self) -> Result:
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
        self.permissions = []
        file = open(fname, 'r')
        self.permissions = file.readlines()
        file.close()
    
    # accepts a string, str, which is the permission we're asking for
    # returns a list of strings, which are the usernames of users with that permission, or None
    def get(self, str):
        for i in self.permissions:
            if i.startswith(str):
                return i[len(str):].split()
        return None
    
    def has_permission(self, name, permission: str) -> bool:
        return name in self.get(permission)



class MiniBot:
    def __init__(self):
        self.users = [] # list of type MbUser
        self.per = Permissions('files/permissions')
    
    def is_user(self, userID):
        for u in self.users:
            if u.id == userID:
                return True
        return False
    
    def get_mb_user(self, userID: discord.User) -> MbUser:
        for u in self.users:
            if u.id == userID:
                return u
        return None
    
    # add a Result to the user that submitted it
    def add(self, res: Result, mes: discord.Message):
        # if the submitter isn't already in the system
        userID = mes.author
        if not self.is_user(userID):
            self.users.append(MbUser(userID))

        # add the results to the user's results
        self.get_mb_user(userID).add(res, mes.channel) 

        
    
    # return Result object, if the message is a mini Result
    def check_result(self, message_content: str) -> Result:
        # regular expressions to match the patterns
        url_pattern = r'https://www.nytimes.com/badges/games/mini.html\?d=(\d{4}-\d{2}-\d{2})&t=(\d+)'
        app_pattern = r'I solved the (\d{1,2}/\d{1,2}/\d{4}) New York Times Mini Crossword in (\d{1,2}):(\d{2})'

        # match the patterns
        url_match = re.match(url_pattern, message_content)
        app_match = re.match(app_pattern, message_content)

        if url_match:
            date_str = url_match.group(1)
            date_format = '%Y-%m-%d'
            time = int(url_match.group(2))
        elif app_match:
            date_str = app_match.group(1)
            date_format = '%m/%d/%Y'
            minutes = int(app_match.group(2))
            seconds = int(app_match.group(3))
            time = minutes * 60 + seconds # convert minutes and seconds to seconds
        else:
            return None

        # convert the date string to a datetime.date object
        date = datetime.strptime(date_str, date_format).date()

        # create a Result object and return it
        return Result(date,time)
    # TODO 'say' admin command, so I can make it say whatever I want, in whichever channel I choose
    async def run_command(self, command: Command):
        if len(command.content.split()) == 0:
            return
        command.content = command.content.lower()
        # ------------user commands-----------------------
        user_commands = ['no_congrats', 'yes_congrats', 'no_rekkening', 'yes_rekkening', 'no_leaderboard', 'yes_leaderboard', 'goofy_ratio']
        if command.type == 'user':
            if command.content.split()[0] not in user_commands:
                await command.message.reply('Command not recognized')
                return
            if command.content.split()[0] == 'goofy_ratio' and len(command.content.split() > 1):
                self.get_mb_user(command.user).set_preference(Preference('goofy_ratio', command.content.split()[1]))
            else: # it's 'no_congrats', 'yes_congrats', 'no_rekkening', 'yes_rekkening', 'no_leaderboard', 'yes_leaderboard'
                self.get_mb_user(command.user).set_preference(Preference(command.content.split()[0], 1))
            responses = ['Okay', 'Awesome', 'Sweet', 'Cool', 'Gotcha']
            await command.message.reply(f'{responses[random.randrange(0,len(responses))]}, {command.user.display_name}, preference set.')
            return
        # ---------------admin commands--------------------------
        else:# it's an admin command
            admin_commands = ['say']
            if not self.per.has_permission(command.user.name, 'admin'):
                await command.message.reply('Permission denied.')
                return
            if command.message.reference: # if it's a reply, that means I'm running the command as the user
                referenced_message = await command.message.channel.fetch_message(command.message.reference.message_id)
                self.run_command(Command('user', command.content, referenced_message.author, command.message))
                return
            if command.content.split()[0] not in admin_commands:
                await command.message.reply('Command not recognized')
                return
            if command.content.split()[0] == 'say':
                if not command.content.split()[1]:
                    return
                channel = discord.utils.get(command.message.guild.channels, name=command.content.split()[1])
                if channel:
                    message = ' '.join(command.content.split()[2:]).strip() # message is everything after say <channel>
                    await channel.send(message)
            admin_responses = ['You got it, boss', 'Sure thing, boss']
            await command.message.reply(admin_responses[random.randrange(0,len(admin_responses))])


            
    async def check_command(self, message: discord.Message):
        possible_command_tokens = ['minibot', 'mb']
        possible_admin_command_tokens = ['minibot_admin', 'mb_admin']
        command_token = None
        command = False
        admin_command = False
        for pct in possible_command_tokens:
            if message.content.lower().startswith(pct):
                command_token = pct
                command = True
        
        # If it's in my secret admin channel
        if message.channel.name == 'secret-minibot-commands':
            command_token = ''
            command = True
            admin_command = True
        # If it's an admin command 
        for pact in possible_admin_command_tokens:
            if message.content.lower().startswith(pact):
                command_token = pact
                command = True
                admin_command = True
        
        # if it's a command
        if command:
            await self.run_command(Command('admin' if admin_command else 'user', message.content[len(command_token):], message.author, message))

        
    
        
        
    
    async def feed(self, message: discord.Message):
        r = self.check_result(message.content)

        # if it's a Result
        if r:
             await self.add(r, message)
        else:
            await self.check_command(message)

    # returns a string representation of time - seconds:int -> 'm:ss'
    def format_time(time: int) -> str:
        if time < 60:
            return str(time)
        else:
            return f'{time // 60}:{time % 60}'
        
    async def daily_leaderboard(self, channel: discord.TextChannel):
        message = 'DAILY LEADERBOARD:\n'
        placings = []
        unsorted_placings = []

        # get everyone in an unsorted list of placings
        for u in self.users:
            r = u.get_todays_result()
            if r and not u.get_preference('no_leaderboard'):
                unsorted_placings.append(Placing(u,r))
        # sort the list
        if (len(unsorted_placings) > 0):
            placings = sorted(unsorted_placings, key = lambda x: x.result.time)
            placings.insert(0,'zero')
            # give everyone a place number
            i = 1
            while (i < len(placings)):
                message += f'{i}. {placings[i].user.id.display_name} {self.format_time(placings[i].result.time)}\n'
                placings[i].user.place(i)
                i += 1
            await channel.send(message)


            


# TODO handle data so that it won't be lost when disconnecting and/or restarting
# TODO handle global object properly
# global object
bot = MiniBot() #TODO change so it starts as none, then in on_ready, initialize so it can read in JSON and remember everyone's info

class myClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {client.user}')

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
token_file = open('files/token', 'r')
token = token_file.read()
token_file.close()



# Run the bot
client.run(token)