import discord
from datetime import datetime, timedelta, date
import re
import random
import asyncio
import emoji

# result class
#     date: result date
#     time: time, in seconds that it took to complete the puzzle
class Result:
    def __init__(self, date: datetime.date, time: int):
        self.date = date
        self.time = time
    def __str__(self):
        return f'Date:{self.date}, time: {self.time}'

# preference types:
#     no_congrats
#     no_rekkening
#     no_leaderboard
#     goofy_ratio
class Preference:
    def __init__(self, type: str, value: int):
        self.type = type
        self.value = value
    def __str__(self):
        return f'{self.type}:{self.value}'

# Command class. 
#    type: 'user' | 'admin' 
#    content: just the command (no 'minibot' or 'mb')
#    user: the discord User executing the command.
#    message: discord Message in which the command was sent
class Command:
    def __init__(self, type: str, content: str, user: discord.User, message: discord.Message):
        self.type = type
        self.content = content
        self.user = user
        self.message = message

# user class for MiniBot
#     id: discord API User object
#     results: list of type Result
#     preferences: list of type Preference
#     times_placed: list of number of times placed 1st, 2nd, etc. index 0 will be empty so index 1 is 1st, etc.
class MbUser:
    def __init__(self, id: discord.User):
        self.name = id.name # name is their username
        self.id = id # id is a discord user
        self.results = [] # list of type Result
        self.preferences = [] # list of type Preference
        self.times_placed = [] # number of times placed 1st, 2nd, etc. index 0 will be empty so index 1 is 1st, etc.

    async def add(self, res: Result, chn: discord.TextChannel):
        self.results.append(res)
        self.results = [res for res in self.results if res.date >= date.today()]# remove any results that are from earlier than today
        if res.date > date.today():# if it's tomorrow's puzzle
            await chn.send(f'Great job on tomorrow\'s puzzle, {self.id.display_name}!')
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
        self.preferences.append(preference)

    def get_preferences_string(self):
        string = self.name
        for preference in self.preferences:
            string += ' ' + str(preference)
        return string

    async def congratulate(self, chnl: discord.TextChannel):
        if self.get_preference('no_congrats'):
            return
        file_name = 'files/congratsMessages'
        # if the player has specified a ratio for how often they want to see goofy congratulation messages
        if self.get_preference('goofy_ratio'):
            # if they roll more than their ratio, they get a normal message.
            # if they roll less than or equal to their ratio, they get a goofy one. IDK, this made sense when I wrote it
            if random.randrange(1,11) <= self.get_preference('goofy_ratio').value:
                file_name = 'files/goofyCongratsMessages'
        file = open(file_name, 'r')
        congrats_messages = file.readlines()
        file.close()
        # send a random congratulation message from the appropriate list to the appropriate channel
        message = congrats_messages[random.randrange(0,len(congrats_messages))]
        message = message.replace('uname', self.id.display_name)
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

# placing class for leaderboard
    # user: MbUser
    # result: Result
    # place: place given in leaderboard
class Placing:
    def __init__(self, user: MbUser, result: Result):
        self.user = user
        self.result = result
        self.place = -1


# poorly written class for permissions.
#     permissions is a list of strings
#         each string consists of a permission name, followed by the users that have that permission
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

# TODO write all information out to files every night during daily_leaderboard, and make it so we can read it back in, in case the bot loses power or connection
# bot class.
#     users: list of type MbUser
#     client: discord Client object
class MiniBot:
    def __init__(self, client: discord.Client):
        self.users = [] # list of type MbUser
        self.per = Permissions('files/permissions')
        self.client = client
    
    def is_user(self, userID: discord.User):
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
    async def add(self, res: Result, mes: discord.Message):
        # if the submitter isn't already in the system
        userID = mes.author
        if not self.is_user(userID):
            self.users.append(MbUser(userID))

        # add the results to the user's results
        await self.get_mb_user(userID).add(res, mes.channel) 

    # async def write_to_file(self):
    #     with open('file.yaml', 'w') as yaml_file:
    #         yaml.safe_dump(self.users, yaml_file)
    
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
    
    #TODO make this happen on startup, possibly in on_ready
    # guild ids:
    #   lanes and nuttings: 1177377997993549824
    #   test: 1213896278614745158
    def read_preferences(self):
        guild = self.client.get_guild(1177377997993549824)
        if not guild:
            print('not guild')
            return 1
        file = open('files/preferences', 'r')
        file_contents = file.readlines()
        file.close()
        for line in file_contents:
            # if the line is a comment, do nothing
            if line.startswith('#'):
                continue
            words = line.split()
            # if it's an empty line, do nothing
            if len(words) == 0:
                continue
            name = words[0]
            preferences = words[1:]
            # get the discord user from their name
            duser = discord.utils.get(guild.members, name=name)
            # if we can't find the discord user
            if not duser:
                print('no user found for ' + name)
                continue
            # add them to the system if they're not already in it
            my_user = self.get_mb_user(duser)
            if not my_user:
                my_user = MbUser(duser)
                self.users.append(my_user)
            for preference in preferences:
                pref_tokens = preference.split(':')
                my_user.set_preference(Preference(pref_tokens[0], int(pref_tokens[1])))
            
            
    def write_preferences(self):
        file = open('files/preferences', 'r')
        file_contents = file.readlines()
        file.close()
        # get rid of everything except the comments section
        file_contents = [line for line in file_contents if line.startswith('#')]
        for user in self.users:
            string = user.get_preferences_string() + '\n'
            # if they actually have preferences
            if len(string.split()) > 1:
                file_contents.append(string)
        
        file = open('files/preferences', 'w')
        file.writelines(file_contents)
        file.close()

    #TODO read placings
    #TODO write placings
    #TODO read results
    #TODO write results
    #TODO read all (just calls read placings, results, and preferences)
    #TODO write all (just calls write placings, results, and preferences)
        
    def read_in_info(self):
        self.read_preferences()
    
    #TODO run command, where I can tell the bot to run a bash command, and it prints out the results
    # at this point, command.content doesn't contain 'minibot' or anything like that
    async def run_command(self, command: Command):
        setting_preference = False
        args = args
        if len(args) == 0:
            return
        command_content_original = command.content
        command.content = command.content.lower()
        command_zero = args[0]
        # ------------user commands-----------------------
        user_commands = ['no_congrats', 'yes_congrats', 'no_rekkening', 'yes_rekkening', 'no_leaderboard', 'yes_leaderboard', 'goofy_ratio', 'help', 'h', 'my_preferences', 'mp']
        if command.type == 'user':
            user = self.get_mb_user(command.user)
            if not user:
                self.users.append(MbUser(command.user))
            if command_zero not in user_commands:
                # await command.message.reply('Command not recognized')
                # await self.run_command(Command('user', 'help', user, command.message))
                return
            if command_zero == 'goofy_ratio' and len(args) > 1:
                setting_preference = True
                self.get_mb_user(command.user).set_preference(Preference('goofy_ratio', int(args[1])))
            elif command_zero == 'help' or command_zero == 'h':
                file = open('files/helpMessage', 'r')
                if not file:
                    return
                help_message = file.read()
                file.close()
                await command.message.reply(help_message)
                return
            elif command_zero == 'my_preferences' or command_zero == 'mp':
                preferences_string = self.get_mb_user(command.user).get_preferences_string()
                await command.message.reply(preferences_string)
            else: # it's 'no_congrats', 'yes_congrats', 'no_rekkening', 'yes_rekkening', 'no_leaderboard', 'yes_leaderboard'
                setting_preference = True
                self.get_mb_user(command.user).set_preference(Preference(args[0], 1))
            responses = ['Okay', 'Awesome', 'Sweet', 'Cool', 'Gotcha']
            response = responses[random.randrange(0,len(responses))]
            if setting_preference:
                await command.message.reply(f'{response}, {command.user.display_name}, preference set.')
                self.write_preferences()
            return
        # ---------------admin commands--------------------------
        else:# it's an admin command
            admin_commands = ['say', 'leaderboard', 'lb', 'help', 'h', 'react', 'reply', 'read_info', 'ri', 'add_time', 'at']
            
            if not self.per.has_permission(command.user.name, 'admin'):
                await command.message.reply('Permission denied.')
                return
            if command_zero == 'add_time' or command_zero == 'at':
                if len(args) < 4:
                    await command.message.reply('usage: add_time person day time')
                    return
                duser = discord.utils.get(guild.members, name=args[1])
                if not duser:
                    await command.message.reply('usage: add_time person day time')
                    return
                my_user = self.get_mb_user(duser)
                if not my_user:
                    self.users.append(MbUser(duser))
                if args[2].lower() == 'today':
                    day = date.today()
                elif args[2].lower() == 'tomorrow':
                    day = date.today() + timedelta(1)
                else:
                    await command.message.reply('usage: add_time person day time')
                    return
                #TODO finish this - read in time and add it
                try:
                    if ":" in args[3]:
                        minutes = args[3].split(':')[0]
                        seconds = args[3].split(':')[1]
                    else:
                        seconds = int(args[3])
                except:
                    await command.message.reply('usage: add_time person day time')
                    return
            if command.message.reference: # if it's a reply, that means I'm running the command as the user
                referenced_message = await command.message.channel.fetch_message(command.message.reference.message_id)
                await self.run_command(Command('user', command.content, referenced_message.author, command.message))
                return
            if command_zero not in admin_commands:
                await command.message.reply('Command not recognized')
                return
            if command_zero == 'say':
                if not args[1]:
                    return
                channel = discord.utils.get(command.message.guild.channels, name=args[1])
                if channel:
                    say_channel_length = len(args[0]) + len(args[1]) + 2
                    message = command_content_original[say_channel_length:] # message is everything after say <channel>
                    await channel.send(message)
                else:
                    await command.message.reply('channel not found')
            if command_zero == 'leaderboard' or command_zero == 'lb':
                await self.daily_leaderboard()
            if command_zero == 'help' or command_zero == 'h':
                file = open('files/helpMessageAdmin', 'r')
                if not file:
                    return
                help_message = file.read()
                file.close()
                await command.message.reply(help_message)
                return
            if command_zero == 'react':
                channel = discord.utils.get(command.message.guild.channels, name=args[1])
                if not channel:
                    await command.message.reply('not channel')
                    return
                if (not args[1]) or (not args[2]) or (not args[3]):# if 'react' isn't followed by 2 strings, do nothing
                    await command.message.reply('not enough args. react channel messageID emoji')
                    return
                if not emoji.is_emoji(args[3]):
                    await command.message.reply('not emoji')
                    return
                try:
                    message_to_react = await channel.fetch_message(int(args[2]))
                    await message_to_react.add_reaction(args[3])
                except discord.errors.NotFound:
                    await command.message.reply('discord.errors.NotFound')
            if command_zero == 'reply':
                channel = discord.utils.get(command.message.guild.channels, name=args[1])
                if not channel:
                    await command.message.reply('not channel')
                    return
                if (not args[1]) or (not args[2]) or (not args[3]):# if 'react' isn't followed by 2 strings, do nothing
                    await command.message.reply('not enough args. reply channel messageID newMessage')
                    return
                try:
                    message_to_reply = await channel.fetch_message(int(args[2]))
                    beginning_length = len(args[0]) + len(args[1]) + len(args[2]) + 3
                    await message_to_reply.reply(command.message.content[beginning_length:])
                except discord.errors.NotFound:
                    await command.message.reply('discord.errors.NotFound')
            if command_zero == 'read_info' or command_zero == 'ri':
                self.read_in_info()
            admin_responses = ['You got it, boss', 'Sure thing, boss']
            response = admin_responses[random.randrange(0,len(admin_responses))]
            await command.message.reply(response)


            
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
            command_type = 'admin' if admin_command else 'user'
            content = message.content[len(command_token):]
            author = message.author
            await self.run_command(Command(command_type, content, author, message))

        
    
        
        
    
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
            minutes = time // 60
            seconds = time % 60
            minutes_string = str(minutes)
            zero = '0' if seconds < 10 else ''
            seconds_string = zero + str(seconds)
            return minutes_string + ':' + seconds_string

    # guild ids:
    #   lanes and nuttings: 1177377997993549824
    #   test: 1213896278614745158        
    async def daily_leaderboard(self):
        guild = self.client.get_guild(1177377997993549824)
        if not guild:
            print('guild not found')
            return
        channel = discord.utils.get(guild.channels, name='puzzles')
        if not channel:
            print('channel not found')
            return
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
                message += f'{i}. {placings[i].user.id.display_name}    {MiniBot.format_time(placings[i].result.time)}\n'
                placings[i].user.place(i)
                i += 1
            await channel.send(message)
    



intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)


# TODO handle data so that it won't be lost when disconnecting and/or restarting
# TODO handle global object properly
# global object
bot = MiniBot(client)

# Event handler for when the bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    await daily_scheduler()

# Event handler for messages
@client.event
async def on_message(message):
        # Don't respond to your own message
        if message.author == client.user:
            return
        
        # send the message to the bot 
        await bot.feed(message)

# Schedule the task to run every day at 8 PM
async def daily_scheduler():
    while not client.is_closed():
        # Get current date and time
        current_time = datetime.now()
        
        # Check if it's 8pm
        if current_time.strftime('%H:%M') == '20:00':
            await bot.daily_leaderboard()
        
        # Wait for 1 minute before checking again
        await asyncio.sleep(60)


# bot's token
token_file = open('files/testToken', 'r')# TODO change back
token = token_file.read()
token_file.close()



# Run the bot
# client.loop.create_task(daily_scheduler())
client.run(token)