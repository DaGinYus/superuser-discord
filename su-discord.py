import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='$')
roles_db = {}
token = 

def save_roles(member):
    # accepts Member and adds roles to roles_db if not already present
    name = str(member)
    if name not in roles_db:
        roles_db[name] = member.roles
        print(roles_db) # for testing
        
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@commands.command(pass_context=True)
@commands.has_any_role("sudoers")
async def sudo(ctx, *args):
    # Implementation of UNIX sudo commands, Discord style, used to interact with the server directly
    # 'userdel' kicks a user while 'adduser' sends an invite
    # these two commands should be pretty similar in implementation:
    # parse command -> find user -> perform action on user
    if args[0] == 'userdel':
        if len(args) != 1:
            try:
                uname = args[1:len(args)]
                usr = await commands.MemberConverter().convert(ctx, " ".join(uname))
                print("Kicking " + str(usr))
                print("Saving roles before kicking...")
                save_roles(usr)
                await discord.Member.kick(usr)
                await ctx.send("{} has been kicked!".format(usr))
            except Exception as e:
                await ctx.send("error: {}".format(e))
        else:
            await ctx.send("userdel: incorrect number of arguments ({})".format(len(args)))
    elif args[0] == 'useradd':
        if len(args) != 1:
            try:
                uname = args[1:len(args)]
                usr = await commands.UserConverter().convert(ctx, " ".join(uname))
                print("Sending invite to: " + str(usr))
                for channel in ctx.guild.text_channels:
                    # looks for welcome channel, otherwise just creates invite to general
                    if "welcome" in channel.name.lower():
                        invite = await channel.create_invite(max_uses=1)
                    elif "general" in channel.name.lower():
                        invite = await channel.create_invite(max_uses=1)
                await usr.send(invite.url)
                await ctx.send("{} has been invited to #{}".format(usr, channel.name))
            except Exception as e:
                await ctx.send("error: {}".format(e))
        else:
            await ctx.send("useradd: incorrect number of arguments ({})".format(len(args)))
    elif args[0] == 'id':
        if len(args) != 1:
            try:
                if args[1] == '--restore' or args[1] == '--save':
                    uname = args[2:len(args)]
                else:
                    uname = args[1:len(args)]
                usr = await commands.MemberConverter().convert(ctx, " ".join(uname))
                usr_name = str(usr)
                msg = discord.Embed(color=0x02dda3)
                if args[1] == '--save':
                    save_roles(usr)
                if (len(roles) == 1 and args[1] == '--restore'):
                    new_roles = roles_db[usr_name]
                    new_roles.pop(0)
                    for role in new_roles:
                        await usr.add_roles(role)
                roles = usr.roles
                roles_str = ""
                for role in roles:
                    roles_str += (role.name + "\n")
                msg.add_field(name="{}'s roles:".format(usr_name), value=roles_str, inline=False)
                await ctx.send(embed=msg)
                print(roles)
            except Exception as e:
                await ctx.send("error: {}".format(e))
    else:
        await ctx.send("{}: command not found".format(args[0]))

@commands.command(pass_context=True)
async def superuser(ctx, *args):
    # Used for commands that don't interact with server but with the bot itself
    # 'help' returns list of commands
    if args[0] == 'help':
        msg = discord.Embed(color=0x02dda3)
        msg.add_field(name="$sudo userdel (user)", value="Kicks user from server", inline=False)
        msg.add_field(name="$sudo useradd (user)", value="Sends an invite to user (prioritizes welcome channel)", inline=False)
        msg.add_field(name="$sudo id [--restore] [--save] (user)", value="Shows the roles of a user\n [--restore] will assign them their previous roles\n [--save] will write their current roles", inline=False)
        msg.add_field(name="$superuser help", value="Show this help menu", inline=False)
        await ctx.send(embed=msg)

@sudo.error
async def sudo_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("{} is not in the sudoers file. This incident will be reported.".format(ctx.message.author))

bot.add_command(sudo)
bot.add_command(superuser)
bot.run(token)
