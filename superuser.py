import json
import re

import discord
from discord.ext import commands


# FEATURES
# Ability to kick, invite, save and assign roles using commands
#  + Roles saved as dictionary of names corresponding to list of ID's for
#    writing to JSON & converted to discord Roles for manipulation
# Read and write changes to JSON file
# Parse commands with flags
#
# COMMANDS
# userdel @[user]: kick user
# adduser [user]#[discriminator]: invite user
# id [-s][-r]: show user roles [-s] means save [-r] means restore
# defaults write [setting] [value]: change setting
# defaults read: show settings
# help: display a help menu
#
# SAMPLE DATA FORMAT
# {
#     "token": "token string",
#     "settings": {"setting1": true, "setting2": false},
#     "roles": {"user1": [role id integer]}
# }


class DataHandler:

    def __init__(self):
        self.CONFIG_PATH = "config.json"
        self.ROLES_PATH = "roles.json"

    def read(self, path):
        try:
            with open(path) as infile:
                data = json.load(infile)
                for item in data:
                    setattr(self, item, data[item])
            print(path + " read successfully")
            return True
        except IOError as e:
            print("IOError: could not open file: {}".format(e))
        except json.JSONDecodeError as e:
            print("JSONDecodeError: invalid JSON file: {}".format(e))

    def write(self, path, content):
        try:
            with open(path) as outfile:
                data = json.dumps(content, outfile, indent=4)
            print(path + " written successfully")
        except IOError as e:
            print("Error: could not open file: {}".format(e))
        except json.JSONDecodeError as e:
            print("Error: invalid JSON format: {}".format(e))


class Commands(object):

    def __init__(self, ctx):
        self.CUSTOM_KICK_MSG = {"DevilStuff#6725": "The evil has been defeated!",
                           "bigboianimetrap#5464": "You have been spanked by daddy"
        		   }
        self.CUSTOM_JOIN_MSG = {"DevilStuff#6725": "An evil has been summoned"}
        self._ctx = ctx
        
    async def userdel(self, user=None, **kwargs):
        if user:
            usr = await commands.MemberConverter().convert(self._ctx, user)
        else:
            raise discord.DiscordException("username could not be converted")
        uname = str(usr)
        print("Kicking " + uname)
        await discord.Member.kick(usr)
        if uname in self.CUSTOM_KICK_MSG:
            await self._ctx.send(self.CUSTOM_KICK_MSG[uname])
        else:
            await self._ctx.send(uname + " has been kicked!")
        
    async def adduser(self, user=None, **kwargs):
        if user:
            usr = await commands.UserConverter().convert(self._ctx, user)
        else:
            raise discord.DiscordException("username could not be converted")
        uname = str(usr)
        print("Sending invite to " + uname)
        channel = self._ctx.guild.system_channel
        if channel is not None:
            invite = await channel.create_invite(max_uses=1)
            await usr.send(invite.url)
            if uname in self.CUSTOM_JOIN_MSG:
                await self._ctx.send(self.CUSTOM_JOIN_MSG[uname])
            else:
                await self._ctx.send(uname + " has been invited to #" + channel.name)
        else:
            raise discord.DiscordException("no available channel to send invite from.")

    async def id(self, user=None, flag=None, data=None,  **kwargs):
        ...

    async def defaults(self):
        ...

    async def return_error(self, err):
        print("Error: {}".format(err))
        await self._ctx.send("Error: {}".format(err))

    def parse(self, arg):
        tokens = {"user": None, "flag": None, "rw": None,"option": None, "value": None}
        rules = re.compile(r"""
            (?P<cmd>^\b[a-z]+\b)                                 # '...' (first word only) ----- command
            (?:\s(?P<user>(?:\w+\#\d+)|(?:<(?:@|@!)[0-9]+>)$)    # '@...' (end word only) ------ user
            |\s(?P<flag>-[a-z])                                  # '-.' ------------------------ flag
            |\s(?P<rw>\bread\b|\bwrite\b)                        # 'read' or 'write' ----------- read or write option
            |\s(?P<option>\b\w+\b(?!$))                          # '...' (not last word) ------- option to set
            |\s(?P<value>\b\w+\b$))+                             # '...' (end word) ------------ value for option
            """, re.VERBOSE)
        if rules.search(arg):
            parsedarg = rules.search(arg)
        else:
            raise AttributeError("regex failed to parse input: No match!")
        for token in tokens:
            if parsedarg.group(token):
                tokens[token] = parsedarg.group(token)
        return parsedarg.group("cmd"), tokens
            
    async def __call__(self, arg, bot_data):
        print("\n" + arg)
        try:
            command, kwargs = self.parse(arg)
            cmd = getattr(self, command)
            if callable(cmd):
                await cmd(data=bot_data, **kwargs)
        except AttributeError as e:
            await self.return_error(e)
        except commands.errors.CommandInvokeError as e:
            await self.return_error(e)
        except discord.DiscordException as e:
            await self.return_error(e)
    

@commands.command(pass_context=True)
@commands.has_any_role("sudoers")
async def sudo(ctx, *, arg):
    cmd = Commands(ctx)
    await cmd(arg, bot_data)

bot = commands.Bot(command_prefix="$")

bot_data = DataHandler()
if bot_data.read(bot_data.CONFIG_PATH) and bot_data.read(bot_data.ROLES_PATH):
    @bot.event
    async def on_ready():
        print("\nLogged in as:")
        print(bot.user.name)
        print(bot.user.id)
        print("------")

    bot.add_command(sudo)
    bot.run(bot_data.token)
