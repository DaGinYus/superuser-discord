import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='$')

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@commands.command(pass_context=True)
@commands.has_any_role("sudoers")
async def sudo(ctx, *args):
    if args[0] == 'userdel':
        if len(args) != 1:
            try:
                uname = args[1:len(args)]
                usr = await commands.MemberConverter().convert(ctx, " ".join(uname))
                print("Kicking " + str(usr))
                await discord.Member.kick(usr)
                await ctx.send("{} has been kicked!".format(usr))
            except Exception as e:
                await ctx.send("error: {}".format(e))
        else:
            await ctx.send("userdel: incorrect number of arguments ({})".format(len(args)))
    else:
        await ctx.send("{}: command not found".format(args[0]))

@sudo.error
async def sudo_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("{} is not in the sudoers file. This incident will be reported.".format(ctx.message.author))

bot.add_command(sudo)
bot.run('NDYzNTAzNzczNDQ5NTg0NjUy.DhxbwQ.4Cj3yKotktI3ITgAD7ZT6nYoCL0')
