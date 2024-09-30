import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import os
from keep_alive import keep_alive

# Keep the bot alive on external services
keep_alive()

# Set up bot intents and bot initialization
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
ROLE_ID = 1278431024556281947
GUILD_ID = 1276712128505446490
LOGS_CHANNEL_ID = 1278458636917670010
PLAY_CHANNEL_ID = 1278455220300677194
INFO_CHANNEL_ID = 1289727948110303253  # ID الشات الذي سيرسل فيه المعلومات العامة
DETECTED_ROLE_NAME = "SCRIPT DETECTED ✅"
PUNISH_DURATION = timedelta(hours=10)  # 10 hours

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

            # Notify the user and log in the INFO_CHANNEL
            await target.send(f"You have been isolated for 10 hours due to suspected script usage.")
            
            # إرسال المعلومات في الشات الذي تم تحديده (المعلومات العامة)
            info_channel = bot.get_channel(INFO_CHANNEL_ID)
            if info_channel:
                await info_channel.send(f"User {target.display_name} was targeted by {ctx.author.display_name}. Action: Script Detected ✅")
            
            # إرسال التفاصيل الدقيقة (التوقيت) إلى الأونر في الخاص
            owner = ctx.guild.owner
            if owner:
                time_diff = (now - last_message_time).total_seconds()
                await owner.send(f"Script detected for {target.display_name}. Time difference: {time_diff} seconds.")
        else:
            await ctx.send("The detection role does not exist.")
    else:
        await ctx.send(embed=create_embed(ctx.author, target, detected=False))
        # إرسال المعلومات العامة للشات المحدد
        info_channel = bot.get_channel(INFO_CHANNEL_ID)
        if info_channel:
            await info_channel.send(f"User {target.display_name} was targeted by {ctx.author.display_name}. Action: Script Detected ❌")

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

# Start checking punishments
check_punishments.start()

if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    if TOKEN is None:
        raise ValueError("No token found! Please set the DISCORD_BOT_TOKEN environment variable.")
    bot.run(TOKEN)
