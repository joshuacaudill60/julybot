"""
An extremely basic Discord bot.
"""

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ROLE_MSG_ID = os.getenv(
    "ROLE_MSG_ID"
)  # ID of the message that can be reacted to to add/remove a role.
RED_ROLE_ID = os.getenv("RED_ROLE_ID")
BLUE_ROLE_ID = os.getenv("BLUE_ROLE_ID")
GREEN_ROLE_ID = os.getenv("GREEN_ROLE_ID")
ORANGE_ROLE_ID = os.getenv("ORANGE_ROLE_ID")
PURPLE_ROLE_ID = os.getenv("PURPLE_ROLE_ID")
YELLOW_ROLE_ID = os.getenv("YELLOW_ROLE_ID")

EMOJI_TO_ROLE = {
    discord.PartialEmoji(
        name="🔴"
    ): RED_ROLE_ID,  # ID of the role associated with unicode emoji '🔴'.
    discord.PartialEmoji(
        name="🔵"
    ): BLUE_ROLE_ID,  # ID of the role associated with unicode emoji '🔵'.
    discord.PartialEmoji(
        name="🟢"
    ): GREEN_ROLE_ID,  # ID of the role associated with unicode emoji '🟢'.
    discord.PartialEmoji(
        name="🟠"
    ): ORANGE_ROLE_ID,  # ID of the role associated with unicode emoji '🟠'.
    discord.PartialEmoji(
        name="🟣"
    ): PURPLE_ROLE_ID,  # ID of the role associated with unicode emoji '🟣'.
    discord.PartialEmoji(
        name="🟡"
    ): YELLOW_ROLE_ID,  # ID of the role associated with unicode emoji '🟡'.
}

INTENTS = discord.Intents.default()
INTENTS.members = True
INTENTS.message_content = True

bot = commands.Bot(command_prefix=".", intents=INTENTS)


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
    Gives a role based on a reaction emoji.
    """
    # Make sure that the message the user is reacting to is the one we care about.
    if payload.message_id != ROLE_MSG_ID:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        # Check if we're still in the guild and it's cached.
        return

    try:
        role_id = EMOJI_TO_ROLE[payload.emoji]
    except KeyError:
        # If the emoji isn't the one we care about then exit as well.
        return

    role = guild.get_role(role_id)
    if role is None:
        # Make sure the role still exists and is valid.
        return

    try:
        # Finally, add the role.
        await payload.member.add_roles(role)
    except discord.HTTPException:
        # If we want to do something in case of errors we'd do it here.
        pass


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    """
    Removes a role based on a reaction emoji.
    """
    # Make sure that the message the user is reacting to is the one we care about.
    if payload.message_id != ROLE_MSG_ID:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        # Check if we're still in the guild and it's cached.
        return

    try:
        role_id = EMOJI_TO_ROLE[payload.emoji]
    except KeyError:
        # If the emoji isn't the one we care about then exit as well.
        return

    role = guild.get_role(role_id)
    if role is None:
        # Make sure the role still exists and is valid.
        return

    # The payload for `on_raw_reaction_remove` does not provide `.member`
    # so we must get the member ourselves from the payload's `.user_id`.
    member = guild.get_member(payload.user_id)
    if member is None:
        # Make sure the member still exists and is valid.
        return

    try:
        # Finally, remove the role.
        await member.remove_roles(role)
    except discord.HTTPException:
        # If we want to do something in case of errors we'd do it here.
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
