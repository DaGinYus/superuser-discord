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
# id [-s][-r][-a]: show user roles [-s] means save [-a] means assign [-r] means restore
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
        self.CONFIG = "config.json"
        self.config_keys = []

    def read(self):
        try:
            with open(self.CONFIG) as infile:
                data = json.load(infile)
                for item in data:
                    setattr(self, item, data[item])
                    self.config_keys.append(item)
            print(self.CONFIG + " read successfully")
            return True
        except IOError as e:
            print("IOError: could not open file: {}".format(e))
        except json.JSONDecodeError as e:
            print("JSONDecodeError: invalid JSON format: {}".format(e))

    def write(self):
        try:
            out = {}
            for item in self.config_keys:
                out[item] = getattr(self, item)
            with open(self.CONFIG, "w") as outfile:
                json.dump(out, outfile, indent=4)
            print(self.CONFIG + " written successfully")
        except IOError as e:
            print("Error: could not open file: {}".format(e))
        except json.JSONDecodeError as e:
            print("Error: invalid JSON format: {}".format(e))


class Commands(object):

    def __init__(self, ctx):
        self.CUSTOM_KICK_MSG = {"DevilStuff#6725": "The evil has been defeated!",
                           "bigboianimetrap#5464": "Allen has been spanked by Daddy"
        		   }
        self.CUSTOM_JOIN_MSG = {"DevilStuff#6725": "An evil has been summoned"}
        self._ctx = ctx
        
    async def userdel(self, user=None, **kwargs):
        if not user:
            raise ValueError("invalid username format")
        usr = await commands.MemberConverter().convert(self._ctx, user)
        uname = str(usr)
        print("Kicking " + uname)
        await discord.Member.kick(usr)
        if uname in self.CUSTOM_KICK_MSG:
            await self._ctx.send(self.CUSTOM_KICK_MSG[uname])
        else:
            await self._ctx.send(uname + " has been kicked!")
        
    async def adduser(self, user=None, **kwargs):
        if not user:
            raise ValueError("invalid username format")
        usr = await commands.UserConverter().convert(self._ctx, user)
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
            raise discord.DiscordException("no available channel to send invite from")

    async def id(self, user=None, flag=None, value=None, data=None, **kwargs):
        if not user:
            raise ValueError("invalid username format")
        async def save():
            usr_roles = usr.roles
            role_list = []
            for role in usr_roles:
                role_list.append(str(role.id))
            data.roles[uname] = role_list
            data.write()
            await self._ctx.send("successfully saved roles")

        async def restore():
            data.read()
            saved_roles = data.roles
            if uname in saved_roles:
                for role in saved_roles[uname]:
                    converted_role = await commands.RoleConverter().convert(self._ctx, role)
                    if converted_role is not self._ctx.guild.default_role:
                        await usr.add_roles(converted_role)
                await self._ctx.send("roles restored")
            else:
                raise discord.DiscordException("could not add roles: user's roles have not been saved")

        async def assign():
            if value.isdigit():
                new_role = await commands.RoleConverter().convert(self._ctx, int(value))
            else:
                converted_value = re.sub(r'"', "", value) # remove quotes if it contains them
                new_role = await commands.RoleConverter().convert(self._ctx, converted_value)
            await usr.add_roles(new_role)
            await self._ctx.send("successfully added role")

        async def show_roles():
            roles_string = ""
            for role in usr.roles:
                roles_string += (role.name + "\n")
            if roles_string == "":
                roles_string = "no roles"
            msg = discord.Embed(color=0x02dda3)
            msg.add_field(name="{}'s roles:".format(uname), value=roles_string, inline=False)
            await self._ctx.send(embed=msg)

        usr = await commands.MemberConverter().convert(self._ctx, user)
        uname = str(usr)

        if flag:
            dispatch = {"-s": save, "-r": restore, "-a": assign}
            await dispatch[flag]()
        await show_roles()

    async def defaults(self, data=None, mode=None, value=None, option=None, **kwargs):
        DESCRIPTIONS = {"start_cache": ("BOOL", "Save roles on bot startup (specify true/false)")}
        
        if mode == "read":
            msg = discord.Embed(title= "superuser settings:", color=0x02dda3)
            for setting in data.settings:
                msg.add_field(name=setting, value=DESCRIPTIONS[setting][1], inline=False)
            await self._ctx.send(embed=msg)
            
        elif mode == "write":
            
            

    async def help(self, **kwargs):
        HELP_MSG = {"userdel": ("(user)", "Kicks user from server"),
                    "adduser": ("(user)", "Sends invite to user"),
                    "id": ("[-r][-s][-a] (user)", "Shows the roles of a user\n"
                           "[-r] will assign them their last saved roles\n"
                           "[-s] will save their roles to file\n"
                           "[-a] will assign them an existing role\n"),
                    "defaults": ("write (option) (value)", "Edits bot setting (use read to see available settings)"),
                    "defaults": ("read", "Shows available settings"),
                    "help": ("", "Shows this help menu")}
        msg = discord.Embed(title="superuser help:", color=0x02dda3)
        for command in HELP_MSG:
            msg.add_field(name=command + " " + HELP_MSG[command][0], value=HELP_MSG[command][1], inline=False)
        await self._ctx.send(embed=msg)

    def parse(self, arg):
        tokens = {"user": None, "flag": None, "mode": None,"option": None, "value": None}
        rules = re.compile(r"""
            (?P<cmd>^\b[a-z]+\b)                                 # '...' (first word only) ---- command
            (?:\s(?P<user>(?:\w+\#\d+)|(?:<(?:@|@!)[0-9]+>))     # '@...' (end word only) ----- user
            |\s(?P<flag>-[a-z])                                  # '-.' ----------------------- flag
            |\s(?P<mode>\bread\b|\bwrite\b)                      # 'read' or 'write' ---------- r/w mode
            |\s(?P<option>\b\w+\b(?!$))                          # '...' (not last word) ------ option to set
            |\s(?P<value>(?:\b\w+\b$)|(?:["\w ]+$))|(?:))+       # '...' (end word) ----------- value for option
            """, re.VERBOSE)
        if rules.search(arg):
            parsedarg = rules.search(arg)
        else:
            raise AttributeError("regex failed to parse input: invalid syntax!")
        for token in tokens:
            if parsedarg.group(token):
                tokens[token] = parsedarg.group(token)
        return parsedarg.group("cmd"), tokens
            
    async def __call__(self, arg, bot_data):
        print("\n" + arg)
        command, kwargs = self.parse(arg)
        kwargs["data"] = bot_data
        cmd = getattr(self, command)
        if callable(cmd):
            await cmd(**kwargs)
    

@commands.command(pass_context=True)
@commands.has_any_role("sudoers")
async def sudo(ctx, *, arg):
    cmd = Commands(ctx)
    await cmd(arg, bot_data)

@sudo.error
async def sudoError(ctx, err):
    if isinstance(err, commands.CheckFailure):
        await ctx.send("{} is not in the sudoers file. This incident will be reported.".format(ctx.message.author))
    print("Error: {}".format(err))
    await ctx.send("Error: {}".format(err))

bot = commands.Bot(command_prefix="$")

bot_data = DataHandler()
if bot_data.read():
    @bot.event
    async def on_ready():
        print("\nLogged in as:")
        print(bot.user.name)
        print(bot.user.id)
        print("------")

    bot.add_command(sudo)
    bot.run(bot_data.token)
