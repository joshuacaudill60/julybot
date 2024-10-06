"""
An extremely basic Discord bot.
"""

import asyncio
import os
import re
import urllib.parse
import urllib.request

import discord
import yt_dlp
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

ROLE_MSG_ID = 1283896815074152528

EMOJI_TO_ROLE = {
    discord.PartialEmoji(
        name="🔴"
    ): 1283840971519299657,  # ID of the role associated with unicode emoji '🔴'.
    discord.PartialEmoji(
        name="🔵"
    ): 1283844488858439804,  # ID of the role associated with unicode emoji '🔵'.
    discord.PartialEmoji(
        name="🟢"
    ): 1283844549353013279,  # ID of the role associated with unicode emoji '🟢'.
    discord.PartialEmoji(
        name="🟠"
    ): 1283844397062164540,  # ID of the role associated with unicode emoji '🟠'.
    discord.PartialEmoji(
        name="🟣"
    ): 1283844512208257074,  # ID of the role associated with unicode emoji '🟣'.
    discord.PartialEmoji(
        name="🟡"
    ): 1283841061705355387,  # ID of the role associated with unicode emoji '🟡'.
}

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix=".", intents=INTENTS)

QUEUES = {}
VOICE_CLIENTS = {}
VT_BASE_URL = "https://www.youtube.com/"
YT_RESULTS_URL = VT_BASE_URL + "results?"
YT_WATCH_URL = VT_BASE_URL + "watch?v="
YT_DL_OPT = {"format": "bestaudio/best"}
YTDL = yt_dlp.YoutubeDL(YT_DL_OPT)

ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": '-vn -filter:a "volume=0.25"',
}


async def play_next(ctx):
    """
    Plays the next song in queue
    """
    if QUEUES[ctx.guild.id] != []:
        link = QUEUES[ctx.guild.id].pop(0)  # Pop the next song in queue
        await play(ctx, link=link)


@bot.command()
async def skip(ctx):
    """
    Skips the current song
    """
    VOICE_CLIENTS[ctx.guild.id].stop()  # Stop playing music
    play_next(ctx) # Play the next song in queue

@bot.command()
async def play(ctx, *, link):
    """
    Plays the song
    """
    try:
        voice_client = await ctx.author.voice.channel.connect()
        VOICE_CLIENTS[voice_client.guild.id] = voice_client
    except Exception as e:
        print(e)

    try:

        if VT_BASE_URL not in link:
            query_string = urllib.parse.urlencode({"search_query": link})

            content = urllib.request.urlopen(YT_RESULTS_URL + query_string)

            search_results = re.findall(r"/watch\?v=(.{11})", content.read().decode())

            link = YT_WATCH_URL + search_results[0]

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: YTDL.extract_info(link, download=False)
        )

        song = data["url"]
        player = discord.FFmpegOpusAudio(song, **ffmpeg_options)

        VOICE_CLIENTS[ctx.guild.id].play(
            player,
            after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop),
        )
    except Exception as e:
        print(e)


@bot.command()
async def clear_queue(ctx):
    """
    Clears the queue
    """
    if ctx.guild.id in QUEUES:
        QUEUES[ctx.guild.id].clear()  # Clear the queue if it is not empty
        await ctx.send("Queue cleared!")
    else:
        await ctx.send("There is no queue to clear!")


@bot.command(name="pause")
async def pause(ctx):
    """
    Pauses the song
    """
    try:
        VOICE_CLIENTS[ctx.guild.id].pause()  # Pause the song
    except Exception as e:
        print(e)


@bot.command(name="resume")
async def resume(ctx):
    """
    Resumes the song
    """
    try:
        VOICE_CLIENTS[ctx.guild.id].resume()  # Resume the song
    except Exception as e:
        print(e)


@bot.command(name="stop")
async def stop(ctx):
    """
    Stops the music
    """
    try:
        VOICE_CLIENTS[ctx.guild.id].stop()  # Stop playing music
        await VOICE_CLIENTS[ctx.guild.id].disconnect()  # Disconnect from VC
        del VOICE_CLIENTS[ctx.guild.id]  # Delete the voice client
    except Exception as e:
        print(e)


@bot.command(name="queue")
async def queue(ctx, *, url):
    """
    Queues a song
    """
    if ctx.guild.id not in QUEUES:
        QUEUES[ctx.guild.id] = []
    QUEUES[ctx.guild.id].append(url)
    await ctx.send("Added to queue!")


@bot.event
async def on_ready():
    """
    Prints message when bot is ready
    """
    print("[+] julybot is ready")


@bot.event
async def on_member_join(member):
    """
    Sends a message when a member joins
    """
    guild = member.guild
    if guild.system_channel is not None:
        to_send = f"Welcome {member.mention} to {guild.name}!"
        await guild.system_channel.send(to_send)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """
    Gives a role based on a reaction emoji
    """
    # Make sure that the message the user is reacting to is the one we care about
    if payload.message_id != ROLE_MSG_ID:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        # Check if we're still in the guild and it's cached
        return

    try:
        role_id = EMOJI_TO_ROLE[payload.emoji]
    except KeyError:
        # If the emoji isn't the one we care about then exit as well
        return

    role = guild.get_role(role_id)
    if role is None:
        # Make sure the role still exists and is valid
        return

    try:
        # Finally, add the role
        await payload.member.add_roles(role)
    except discord.HTTPException:
        # If we want to do something in case of errors we'd do it here
        pass


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """
    Removes a role based on a reaction emoji
    """
    # Make sure that the message the user is reacting to is the one we care about
    if payload.message_id != ROLE_MSG_ID:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        # Check if we're still in the guild and it's cached
        return

    try:
        role_id = EMOJI_TO_ROLE[payload.emoji]
    except KeyError:
        # If the emoji isn't the one we care about then exit as well
        return

    role = guild.get_role(role_id)
    if role is None:
        # Make sure the role still exists and is valid
        return

    # The payload for `on_raw_reaction_remove` does not provide `.member`
    # so we must get the member ourselves from the payload's `.user_id`
    member = guild.get_member(payload.user_id)
    if member is None:
        # Make sure the member still exists and is valid
        return

    try:
        # Finally, remove the role
        await member.remove_roles(role)
    except discord.HTTPException:
        # If we want to do something in case of errors we'd do it here
        pass


@bot.command()
@commands.has_permissions(send_messages=True)
@commands.cooldown(1, 5, commands.BucketType.user)
async def echo(ctx, msg: str):
    """
    Echos input
    """
    await ctx.send(msg)


@echo.error
async def echo_error(ctx, error):
    """
    Handles echo errors
    """
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("You must specify a message to echo.")
    elif isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("You need send messages permissions to do this!")
    elif isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(error)
    else:
        raise error


@bot.command()
@commands.has_permissions(manage_messages=True)
@commands.cooldown(1, 5, commands.BucketType.user)
async def purge(ctx, num_msgs: int):
    """
    Purges a specified number of messages
    """
    await ctx.defer()
    await ctx.channel.purge(limit=num_msgs)


@purge.error
async def purge_error(ctx, error):
    """
    Handles purge errors
    """
    if isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send("You must specify the number of messages to purge.")
    if isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("You need manage messages permissions to do this!")
    elif isinstance(error, commands.errors.CommandOnCooldown):
        await ctx.send(error)
    else:
        raise error


if __name__ == "__main__":
    # Runs the Discord bot.
    bot.run(DISCORD_TOKEN)
