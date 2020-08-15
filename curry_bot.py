from discord import Game, Status
from discord.ext.commands import Bot

from bingo.bingo import get_room
from discord_tools.auth import get_token
from discord_tools.discord_formatting import *
from speedrunapi.speedrunapi import *

import re
import time
import math


TOKEN = get_token()
RANDO_BASE = 'https://adrando.com/'
RANDO_LINKS = ['https://adrando.com/']
client = Bot(command_prefix='!', status=Status.online, activity=Game("Azure Dreams"))
BOT_ID = '631144975366619146'
COUNTDOWN_START = 10
SEEDS_TO_GENERATE = 3
MAX_SEEDS = 7
NULL_PRESET = ""
RANDO_PRESETS = { \
                    'secondTower': 'Only Second Tower', \
                    'secondTowerRun': 'Speedrun Second Tower', \
                    'starsTournament': 'STARS Tournament', \
                    'tournament': 'RM3T #2 Tournament' \
                }

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


@client.command(description="Crystal Curry", brief="Curry")
async def curry(ctx):
    await ctx.send(curry_message("The crystallization of the spices pop up here and there like crystal balls."))
    await ctx.send(curry_message("The curry made here is not aiming to be the high class curry at your common Indian restaurant,"))
    await ctx.send(curry_message("but more something you would enjoy at home, bringing out that homely flavor."))
    await ctx.send(curry_message("It's a taste that does not discriminate, that is fit for everyone."))
    await ctx.send(curry_message("Having said that, though, it's not something that you could make at home."))
    await ctx.send(curry_message("The smoothness and depth in it's taste is something only a professional chef could possibly make."))
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
    global RANDO_LINKS
    print_links = True
    if len(args) >= 1:
        # Match on the start to make this command respond to 'presets' as well
        if args[0].startswith('preset'):
            print_links = False
            await ctx.send('\n'.join(curry_message("Preset: {}, Description: {}".format(preset, description))) for preset, description in RANDO_PRESETS.items())
        else:
            updated = False
            preset = get_matching_preset(args[0])
            if preset:
                quantity = SEEDS_TO_GENERATE
                if len(args) >= 2:
                    if args[1].isdigit():
                        user_quantity = int(args[1])
                        if user_quantity <= 0 or user_quantity > MAX_SEEDS:
                            await ctx.send(curry_message("Number of seeds is limited to {}.".format(SEEDS_TO_GENERATE)))
                        else:
                            quantity = user_quantity
                    else:
                        await ctx.send(curry_message("I don't know how to generate {} seeds. Type '!help rando' for help.".format(args[1])))
                await ctx.send(curry_message("Generating {} {} seeds...".format(quantity, RANDO_PRESETS[preset])))
                seed_base = time.time() * 1000
                seed_floor = math.floor(seed_base)
                # Use the nanosecond portion of the time as a pseudo-random offset, plus a constant in case that happens to be 0
                offset = math.floor((seed_base - seed_floor) * 1000) + 50
                RANDO_LINKS = [make_seed(preset, seed_floor - offset * i) for i in range(quantity)]
                updated = True
            elif args[0].startswith(RANDO_BASE):
                RANDO_LINKS = args
                updated = True
            else:
                await ctx.send(curry_message("That doesn't look like a seed or preset. Curry."))
                print_links = False
            await ctx.send(curry_message("Rando seed links {}updated".format("" if updated else "NOT ")))
    if print_links:
        await ctx.send(curry_message("Current rando seed links:"))
        for i, link in enumerate(RANDO_LINKS):
            await ctx.send(curry_message("Seed {}: {}".format(i+1, link)))

def get_matching_preset(param):
    preset = NULL_PRESET
    # This is necessary to handle cases where one preset contains the name of another preset
    if param in RANDO_PRESETS:
        preset = param
    else:
        # Search for partial matches to allow e.g. 'star' to work for 'starsTournament'
        matches = 0
        for key in RANDO_PRESETS.keys():
            if key.startswith(param):
                preset = key
                matches += 1
        if matches != 1:
            preset = NULL_PRESET
    return preset

def make_seed(preset, seed):
    return "{}?P:{},,{}".format(RANDO_BASE, preset, seed)

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

client.run(TOKEN)
