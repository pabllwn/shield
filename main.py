import asyncio
import discord
from discord.ext import commands
from keep_alive import keep_alive
import os

# Start keep-alive function to maintain bot running
keep_alive()

# Set up intents and bot
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration variables
ROLE_ID = 1278431024556281947
GUILD_ID = 1276712128505446490
LOGS_CHANNEL_ID = 1278458636917670010
PLAY_CHANNEL_ID = 1278455220300677194
INFO_CHANNEL_ID = 1289727948110303253  # Example: Set the channel where the bot will send info
DETECTED_ROLE_NAME = "SCRIPT DETECTED ✅"
PUNISH_DURATION = 36000  # 10 hours in seconds

# Store punished users
punished_users = {}

# Function to detect if an event loop is running and start it if not
def ensure_event_loop():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

# Function to calculate the time difference and detect script usage
async def detect_script(ctx, target):
    now = discord.utils.utcnow()
    
    if not target.last_message:
        await ctx.send(f"Cannot detect the last message time for {target.display_name}.")
        return False, 0
    
    last_message_time = target.last_message.created_at
    time_diff = (now - last_message_time).total_seconds()
    
    return time_diff < 1, time_diff

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="discord.gg/diamondsr"))

@bot.command()
async def rob(ctx, target: discord.Member):
    if not target or target == ctx.author:
        await ctx.send("Invalid target.")
        return
    
    # Ensure event loop is running
    ensure_event_loop()

    # Detect script usage
    script_detected, time_diff = await detect_script(ctx, target)
    
    if script_detected:
        role = discord.utils.get(ctx.guild.roles, name=DETECTED_ROLE_NAME)
        if role:
            await target.add_roles(role)
            punished_users[target.id] = discord.utils.utcnow().timestamp() + PUNISH_DURATION
            await ctx.send(f"Script detected for {target.display_name}. ✅")
            
            # Send information in the designated channel
            info_channel = bot.get_channel(INFO_CHANNEL_ID)
            if info_channel:
                await info_channel.send(f"User {target.display_name} was targeted by {ctx.author.display_name}. Script detected: ✅")
            
            # Send time difference to the owner in private
            owner = ctx.guild.owner
            if owner:
                await owner.send(f"Script detected for {target.display_name}. Time difference: {time_diff} seconds.")
            
            # Notify the user
            await target.send(f"You have been punished for 10 hours due to script usage.")
            
            # Remove the role after 10 hours
            await asyncio.sleep(PUNISH_DURATION)
            await target.remove_roles(role)
            await target.send("Your punishment has ended. You can interact again.")
        else:
            await ctx.send("The detection role does not exist.")
    else:
        await ctx.send(f"No script detected for {target.display_name}. ❌")
        # Send information in the designated channel
        info_channel = bot.get_channel(INFO_CHANNEL_ID)
        if info_channel:
            await info_channel.send(f"User {target.display_name} was targeted by {ctx.author.display_name}. Script detected: ❌")

# Command to manually remove the role before 10 hours
@bot.command()
async def done(ctx, target: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=DETECTED_ROLE_NAME)
    if role in target.roles:
        await target.remove_roles(role)
        await ctx.send(f"{target.display_name} has been freed from punishment.")
        await target.send("Your punishment has been manually ended.")
        if target.id in punished_users:
            del punished_users[target.id]
    else:
        await ctx.send(f"{target.display_name} does not have the script detection role.")

if __name__ == "__main__":
    TOKEN = os.getenv("TOKEN")
    if TOKEN is None:
        raise ValueError("No token found! Please set the DISCORD_BOT_TOKEN environment variable.")
    
    bot.run(TOKEN)
