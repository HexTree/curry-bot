from discord import Game, Status
from discord.ext.commands import Bot

from bingo.bingo import get_room
from discord_tools.auth import get_token
from discord_tools.discord_formatting import *
from speedrunapi.speedrunapi import *

import re


TOKEN = get_token()
RANDO_LINKS = ['https://adrando.com/']
client = Bot(command_prefix='!', status=Status.online, activity=Game("Azure Dreams"))
BOT_ID = '631144975366619146'

# EMOJIS
NICOHEY = '<:NicoHey:635538084062298122>'


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
    if BOT_ID in message.content:
        await message.channel.send(curry_message("Hey {} {} Type !help for my commands.".format(get_author(message), NICOHEY)))
    await client.process_commands(message)


@client.command(description="Say Hello", brief="Say Hello")
async def hello(ctx):
    await ctx.send(curry_message("Hello {}!".format(get_author(ctx.message))))


@client.command(description="Creates a Bingo room at https://bingosync.com/ and provides the link and password.", brief="Create a Bingo game")
async def bingo(ctx):
    await ctx.send(curry_message("Creating Bingo room. Please wait a moment..."))
    room_url, password = get_room()
    if not room_url:
        await ctx.send(curry_message("Error! I wasn't able to create the room. Curry."))
    else:
        await ctx.send(curry_message("...done. Room created at URL: {} with password: {}\nGo do your best! Don't stumble!".format(room_url, italics(password))))


@client.command(description="Type '!rando' to fetch the current seed link runners are playing on. Type '!rando <link>' to overwrite current seed with a new one of your choice.", brief="Get rando seed in progress")
async def rando(ctx, *args):
    global RANDO_LINKS
    if len(args) >= 1:
        RANDO_LINKS = args
        await ctx.send(curry_message("Rando seed links updated"))
    await ctx.send(curry_message("Current rando seed links:"))
    for i, link in enumerate(RANDO_LINKS):
        await ctx.send(curry_message("Seed {}: {}".format(i+1, link)))


@client.command(description="Type '!leaderboard <category>' to display the current leaderboard, where category is Any%, Bookless% or 100% (For now, just standard categories)", brief="Fetch requested speedrun leaderboard")
async def leaderboard(ctx, *args):
    if not args:
        await ctx.send(curry_message("No category supplied. Type '!help leaderboard' for more info. Curry."))
    await ctx.send(curry_message("Fetching leaderboard..."))
    leaderboard = fetch_leaderboard(args[0])
    if not leaderboard:
        await ctx.send(curry_message("Something went wrong. Is it a valid category? Type '!help leaderboard' for more info. Curry."))
    else:
        for rank, player, time in leaderboard:
            hours = time//3600
            time%=3600
            mins = str(time//60).zfill(2)
            time%=60
            secs = str(time).zfill(2)
            if hours > 0:
                timestamp = '{}h {}m {}s'.format(hours, mins, secs)
            elif int(mins) > 0:
                timestamp = '{}m {}s'.format(mins, secs)
            else:
                timestamp = '{}s'.format(secs)

            await ctx.send(curry_message("Rank: {}\tRunner: {}\t\tTime: {}".format(rank, player, timestamp)))

client.run(TOKEN)
