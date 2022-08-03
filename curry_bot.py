import random

from discord import Game, Status
from discord.ext.commands import Bot

from ad_rando.seed_generator import RandoCommandHandler
from bingo.bingo import get_room
from common.common import Timestamp
from discord_tools.auth import get_token
from discord_tools.discord_formatting import *
from randomwrapper.randomwrapper import dice_roll
from speedrunapi.speedrunapi import *

import re
import time


TOKEN = get_token()
client = Bot(command_prefix='!', status=Status.online, activity=Game("Azure Dreams"))
BOT_ID = '631144975366619146'
COUNTDOWN_START = 10
SEEDS_TO_GENERATE = 3

# EMOJIS
NICOHEY = '<:NicoHey:635538084062298122>'
HORZASHOOK = '<:Horzashook:717744240670539788>'

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
    elif message.content.lower() in ("good bot", "good bot.", "good bot!"):
        await message.channel.send(curry_message("{}. Aw, shucks!".format(get_author(message))))
    elif message.content.lower() in ("bad bot", "bad bot.", "bad bot!"):
        await message.channel.send(HORZASHOOK)
    elif ("earthquake%" in message.content.lower() or "eq%" in message.content.lower()) and random.random() < 0.5:
        await message.channel.send(curry_message("ANALYSING EARTHQUAKE%..."))
        time.sleep(2)
        await message.channel.send(curry_message("A STRANGE GAME."))
        time.sleep(0.5)
        await message.channel.send(curry_message("THE ONLY WINNING MOVE IS\nNOT TO PLAY."))
        time.sleep(1)
        await message.channel.send(curry_message("HOW ABOUT A NICE GAME OF CURRY%?"))
    elif BOT_ID in message.content:
        await message.channel.send(curry_message("Hey {} {}".format(get_author(message), NICOHEY)))
    await client.process_commands(message)


@client.command(description="Say Hello", brief="Say Hello")
async def hello(ctx):
    await ctx.send(curry_message("Hello {}!".format(get_author(ctx.message))))


@client.command(description="Crystal Curry", brief="Curry")
async def curry(ctx):
    await ctx.send(curry_message("The crystallization of the spices pop up here and there like crystal balls."))
    time.sleep(0.5)
    await ctx.send(curry_message("The curry made here is not aiming to be the high class curry at your common Indian restaurant,"))
    time.sleep(0.5)
    await ctx.send(curry_message("but more something you would enjoy at home, bringing out that homely flavor."))
    time.sleep(0.5)
    await ctx.send(curry_message("It's a taste that does not discriminate, that is fit for everyone."))
    time.sleep(0.5)
    await ctx.send(curry_message("Having said that, though, it's not something that you could make at home."))
    time.sleep(0.5)
    await ctx.send(curry_message("The smoothness and depth in it's taste is something only a professional chef could possibly make."))
    time.sleep(1.5)
    await ctx.send(curry_message("Munch Munch"))


@client.command(description="Creates a Bingo room at https://bingosync.com/ and provides the link and password.", brief="Create a Bingo game")
async def bingo(ctx):
    await ctx.send(curry_message("Creating Bingo room. Please wait a moment..."))
    room_url, password = get_room()
    if not room_url:
        await ctx.send(curry_message("Error! I wasn't able to create the room. Curry."))
    else:
        await ctx.send(curry_message("...done. Room created at URL: {} with password: {}\nGo do your best! Don't stumble!".format(room_url, italics(password))))


@client.command(description="Type '!rando' to fetch the current seed link runners are playing on.\nType '!rando <link>' to overwrite current seed with a new one of your choice.\nType '!rando presets' for a list of presets.\nType '!rando <preset>' to generate {} seeds of the given preset.\nType '!rando <preset> <quantity>' to generate quantity seeds of the given preset.".format(SEEDS_TO_GENERATE), brief="Make or get current rando seeds")
async def rando(ctx, *args):
    responses = RandoCommandHandler(args).handle()
    await ctx.send('\n'.join(curry_message(response) for response in responses))


@client.command(description="Type '!leaderboard <category>' to display the current leaderboard", brief="Fetch requested speedrun leaderboard")
async def leaderboard(ctx, *args):
    if not args:
        await ctx.send(curry_message("No category supplied. Type '!help leaderboard' for more info. Curry."))
    strings = []
    is_name = True
    for output in fetch_leaderboard(' '.join(args)):
        if is_name:
            is_name = False
            await ctx.send(curry_message("Fetching {} leaderboard...".format(output)))
            continue
        rank, player, seconds = output
        strings.append(curry_message("Rank: {}\tRunner: {}\t\tTime: {}".format(rank, player, str(Timestamp.from_milliseconds(seconds*1000)))))
    await ctx.send('\n'.join(strings))


@client.command(description="Type '!countdown' to start a countdown from {}.\nType '!countdown <start>' to countdown from start, where start is a positive integer <= {}.".format(COUNTDOWN_START, COUNTDOWN_START), brief="Start a countdown")
async def countdown(ctx, *args):
    if args and not args[0].isdigit():
        await ctx.send(curry_message("I can't count starting from {}. Curry.".format(args[0])))
    else:
        start = int(args[0]) if args else COUNTDOWN_START
        if start <= 0:
            await ctx.send(curry_message("Why not just say 'go'? Curry."))
        elif start > COUNTDOWN_START:
            await ctx.send(curry_message("That sounds like a lot of work. Ask me to start counting from {} or less. Curry.".format(COUNTDOWN_START)))
        else:
            for n in range(0, start):
                await ctx.send(curry_message("{}".format(start - n)))
                time.sleep(1)
            await ctx.send(curry_message("Go! Curry."))


@client.command(description="Flip a coin, resulting in Heads or Tails. Uses random bits from random.org", brief="Flip a coin")
async def flip(ctx):
    await ctx.send(curry_message("Flipping coin..."))
    if dice_roll(1, 2) == 1:
        await ctx.send(curry_message("Heads :crown:"))
    else:
        await ctx.send(curry_message("Tails :coin:"))


@client.command(description="Roll n-sided dice. For instance '!roll 2d8' rolls two 8-sided dice and sums them. '!roll d20' rolls a 20-sided die. Uses random bits from random.org", brief="Roll dice")
async def roll(ctx, *args):
    if not args:
        await ctx.send(curry_message("No argument supplied. Defaulting to d20..."))
        num, sides = 1, 20
    else:
        arg = args[0].lower()
        dice_pattern = r"^\d*d\d+$"
        if re.match(dice_pattern, arg):
            ints = [int(x) for x in arg.split('d') if x != '']
            num = 1
            if len(ints) > 1:
                num = ints[0]
            sides = ints[-1]
        else:
            await ctx.send(curry_message("Argument format not understood. See '!help roll'."))
            return
    if not (1 <= num <= 100 and 2 <= sides <= 100):
        await ctx.send(curry_message("Numbers must be between 1d2 and 100d100 inclusive!"))
        return
    if num == 1:
        await ctx.send(curry_message("Rolling a d{}...".format(sides)))
    else:
        await ctx.send(curry_message("Rolling {}d{}...".format(num, sides)))
    result = dice_roll(num, sides)
    await ctx.send(curry_message("Result: {}".format(result)))
    if num == 1 and sides == 20 and result == 20:
        await ctx.send(curry_message("Critical hit!"))

# COMMANDS
@client.command(description="About Curry Bot", brief="About Curry Bot")
async def about(ctx):
    await ctx.send(curry_message("Curry Bot is an open-source discord bot, available at https://github.com/HexTree/curry-bot\n")
                   + curry_message("On the GitHub page you can find dev contacts, and submit bug/feedback.\n")
                   + curry_message("The bot is run on an Amazon EC2 instance, 24/7. The server upkeep costs about $6 per month.\n")
                   + curry_message("If you wish to support the running of the Bot, and future updates, you can donate via the following:\n")
                   + curry_message("Ko-fi: <https://ko-fi.com/hextree>\n")
                   + curry_message("Bitcoin: bc1qdw5hfljv5afrcqvm62c6pn5e98q2rvzj9558yx\n"))


client.run(TOKEN)
