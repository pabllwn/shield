import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import os
from flask import Flask
from threading import Thread

# Flask setup
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
ROLE_ID = 1278431024556281947
GUILD_ID = 1276712128505446490
LOGS_CHANNEL_ID = 1278458636917670010
PLAY_CHANNEL_ID = 1278455220300677194
LOG_CHANNEL_NAME = "10-hour-outcast-casino"
DETECTED_ROLE_NAME = "SCRIPT DETECTED ✅"
PUNISH_DURATION = timedelta(hours=10)  # 10 hours
ALLOWED_ROLE_IDS = [1278359492676943912, ]

# Store punished users with expiration times
punished_users = {}

# Get current time with milliseconds
def current_time():
    return datetime.now()

# Compare times and determine if a script is used
def detect_script(last_message_time, current_message_time):
    time_diff = (current_message_time - last_message_time).total_seconds()
    return time_diff < 1  # If the difference is less than a second, likely a script

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="discord.gg/diamondsr"))

    for guild in bot.guilds:
        # Ensure the role exists
        role = discord.utils.get(guild.roles, name=DETECTED_ROLE_NAME)
        if not role:
            await guild.create_role(name=DETECTED_ROLE_NAME, permissions=discord.Permissions.none())
            print(f'Created role {DETECTED_ROLE_NAME}')

        # Ensure the channel exists
        log_channel = discord.utils.get(guild.channels, name=LOG_CHANNEL_NAME)
        if not log_channel:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                discord.utils.get(guild.roles, name=DETECTED_ROLE_NAME): discord.PermissionOverwrite(read_messages=True)
            }
            await guild.create_text_channel(LOG_CHANNEL_NAME, overwrites=overwrites)
            print(f'Created channel {LOG_CHANNEL_NAME}')

# Command to detect and punish script users
@bot.command()
async def rob(ctx, target: discord.Member):
    now = current_time()
    
    if not target or target == ctx.author:
        await ctx.send("Invalid target.")
        return

    # Check if target sent a message recently
    last_message_time = target.last_message.created_at if target.last_message else None
    if not last_message_time:
        await ctx.send(f"Cannot determine last message time for {target.display_name}.")
        return

    # Calculate time difference and detect script
    if detect_script(last_message_time, now):
        role = discord.utils.get(ctx.guild.roles, name=DETECTED_ROLE_NAME)
        if role:
            await target.add_roles(role)
            punished_users[target.id] = now + PUNISH_DURATION
            await ctx.send(embed=create_embed(ctx.author, target, detected=True))

            # Notify the user and log in the special channel
            await target.send(f"You have been isolated for 10 hours due to suspected script usage.")
            log_channel = discord.utils.get(ctx.guild.channels, name=LOG_CHANNEL_NAME)
            if log_channel:
                await log_channel.send(f"{target.display_name} has been detected using a script.")
        else:
            await ctx.send("The detection role does not exist.")
    else:
        await ctx.send(embed=create_embed(ctx.author, target, detected=False))

# Helper function to create a professional embed
def create_embed(executor, target, detected):
    embed = discord.Embed(
        title="Script Detection",
        description=f"Action performed by {executor.mention}",
        color=discord.Color.red() if detected else discord.Color.green()
    )
    embed.add_field(name="Target", value=target.mention, inline=True)
    embed.add_field(name="Script Detected", value="✅ Yes" if detected else "❌ No", inline=True)
    embed.add_field(name="Time", value=f"{datetime.now()}", inline=False)
    return embed

# Task that checks for expired punishments
@tasks.loop(minutes=1)
async def check_punishments():
    now = current_time()
    expired_users = []

    for user_id, end_time in punished_users.items():
        if now >= end_time:
            guild = discord.utils.get(bot.guilds, id=GUILD_ID)
            user = discord.utils.get(guild.members, id=user_id)
            role = discord.utils.get(guild.roles, name=DETECTED_ROLE_NAME)
            if user and role:
                await user.remove_roles(role)
                await user.send(f"Your isolation has ended. You are free to interact again.")
                expired_users.append(user_id)

    for user_id in expired_users:
        del punished_users[user_id]

# Command to manually remove punishment
@bot.command()
async def done(ctx, target: discord.Member):
    if target.id in punished_users:
        role = discord.utils.get(ctx.guild.roles, name=DETECTED_ROLE_NAME)
        if role:
            await target.remove_roles(role)
            del punished_users[target.id]
            await ctx.send(f"{target.display_name} has been freed from isolation.")
            await target.send("Your isolation has been manually ended.")
    else:
        await ctx.send(f"{target.display_name} is not currently isolated.")

# Command for shield functionality
@bot.command()
async def shield(ctx, user: discord.Member):
    if ctx.guild.id != GUILD_ID:
        return

    # Check if the command author has one of the allowed roles
    if not any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles):
        await ctx.send("You do not have permission to use this command.")
        return

    role = discord.utils.get(ctx.guild.roles, id=ROLE_ID)
    logs_channel = discord.utils.get(ctx.guild.text_channels, id=LOGS_CHANNEL_ID)

    if role is None:
        await ctx.send("Role not found. Please check the role ID.")
        return

    if logs_channel is None:
        await ctx.send("Logs channel not found. Please check the logs channel ID.")
        return

    if user is None:
        await ctx.send("User not found. Please check the user ID or mention.")
        return

    try:
        if role in user.roles:
            await ctx.send(f"{user.mention} already has this role! 🛡️ Adding another hour to their time.")
            await logs_channel.send(f"{user.mention} already had the role! Added another hour to their time. ⏳")
        else:
            await user.add_roles(role)
            await ctx.send(f"Role granted to {user.mention}! 🛡️ They now have access to the play channel <#{PLAY_CHANNEL_ID}>.")
            await logs_channel.send(f"{user.mention} has been given the role and access to the play channel <#{PLAY_CHANNEL_ID}>. 🛡️ The role will be removed in one hour.")

        # Schedule role removal after exactly one hour
        await asyncio.sleep(3600)
        if role in user.roles:
            await user.remove_roles(role)
            await ctx.send(f"Role removed from {user.mention} after one hour! ⏳")
            await logs_channel.send(f"{user.mention} had the role removed exactly one hour after being assigned. ⏳")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print(f"Error in shield command: {e}")

# Start checking punishments
check_punishments.start()

# Function to run the bot
async def run_discord_bot():
    TOKEN = os.getenv("TOKEN")
    if TOKEN is None:
        raise ValueError("No token found! Please set the DISCORD_BOT_TOKEN environment variable.")
    await bot.start(TOKEN)

# Main function to run both Flask and Discord bot
def main():
    # Start Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Run Discord bot
    asyncio.run(run_discord_bot())  # Correctly running the bot

if __name__ == "__main__":
    main()
