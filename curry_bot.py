from discord import Game, Status
from discord.ext.commands import Bot

from bingo.bingo import get_room
from discord_tools.auth import get_token
from discord_tools.discord_formatting import *

import re

TOKEN = get_token()
RANDO_LINK = 'N/A'
client = Bot(command_prefix='!', status=Status.online, activity=Game("Azure Dreams"))


# EVENTS
@client.event
async def on_ready():
    print("Logged in as " + client.user.name)


@client.event
async def on_disconnect():
    await client.change_presence(afk=True)
    print("Disconnect")


@client.event
async def on_error(event_method, *args, **kwargs):
    await client.change_presence(afk=True)
    print("Error")


# COMMANDS
@client.command(description="for dev use", brief="(for dev use)")
async def debug(ctx):
    pass


@client.event
async def on_message(message):
    if message.author.bot:
        return
    curry_pattern = r"^curry\W*$"
    if re.match(curry_pattern, message.content.lower()):
        await message.channel.send(curry_message("?????"))
    if '631144975366619146' in message.content:
        await message.channel.send(curry_message("Hey {}. Type !help for my commands.".format(get_author(message))))
    await client.process_commands(message)


@client.command(description="Say Hello", brief="Say Hello")
async def hello(ctx):
    await ctx.send(curry_message("Hello {}!".format(get_author(ctx.message))))


@client.command(description="Creates a Bingo room at https://bingosync.com/ and provides the link and password.", brief="Create a Bingo game")
async def bingo(ctx):
    await ctx.send(curry_message("Creating Bingo room. Please wait a moment..."))
    room_url, password = get_room()
    if not room_url:
        await ctx.send(curry_message("Error! I wasn't able to create the room. Sorry. Sorry. Curry."))
    else:
        await ctx.send(curry_message("...done. Room created at URL: {} with password: {}\nGo do your best! Don't stumble!".format(room_url, italics(password))))


@client.command(description="Type '!rando' to fetch the current seed link runners are playing on. Type '!rando <link>' to overwrite current seed with a new one of your choice.", brief="Get rando seed in progress")
async def rando(ctx, *args):
    global RANDO_LINK
    if len(args) == 1:
        RANDO_LINK = args[0]
        await ctx.send(curry_message("Rando seed link updated"))
    await ctx.send(curry_message("Current rando seed link: {}".format(RANDO_LINK)))

client.run(TOKEN)
