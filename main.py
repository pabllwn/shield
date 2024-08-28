from discord.ext import commands, tasks
import asyncio
import discord
from keep_alive import keep_alive

keep_alive()
intents = discord.Intents.all()
intents.members = True
# Initialize bot
bot = commands.Bot(command_prefix='&', intents=intents)

# Replace with your actual values
ROLE_ID = 1278431024556281947
GUILD_ID = 1276712128505446490
LOGS_CHANNEL_ID = 1278458636917670010
PLAY_CHANNEL_ID = 1278455220300677194

# List of allowed user IDs
ALLOWED_USER_IDS = [826571466815569970, 758076857353502740, 220218739575095296]
@bot.event
async def on_command(ctx):
    if ctx.command.name == 'help':
        return  # يتخطى أو يلغى الأمر `&help`

@bot.command()
async def help(ctx):
    # لا تفعل أي شيء عند استدعاء `&help`
    pass
@bot.event
async def on_ready():
    print(f'Bot is ready and logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="discord.gg/diamondsr"))

@bot.command()
async def shield(ctx, user_id: int):
    if ctx.guild.id != GUILD_ID:
        return

    if ctx.author.id not in ALLOWED_USER_IDS:
        await ctx.send("You do not have permission to use this command.")
        return

    role = discord.utils.get(ctx.guild.roles, id=ROLE_ID)
    logs_channel = discord.utils.get(ctx.guild.text_channels, id=LOGS_CHANNEL_ID)
    user = ctx.guild.get_member(user_id)
    
    if role is None:
        await ctx.send("Role not found. Please check the role ID.")
        return
    
    if logs_channel is None:
        await ctx.send("Logs channel not found. Please check the logs channel ID.")
        return

    if user is None:
        await ctx.send("User not found. Please check the user ID.")
        return

    try:
        if role in user.roles:
            await ctx.send(f"{user.mention} already has this role! 🛡️ Adding another hour to their time.")
            await logs_channel.send(f"{user.mention} already had the role! Added another hour to their time. ⏳")
        else:
            await user.add_roles(role)
            await ctx.send(f"Role granted to {user.mention}! 🛡️ They now have access to the play channel <#{PLAY_CHANNEL_ID}>.")
            await logs_channel.send(f"{user.mention} has been given the role and access to the play channel <#{PLAY_CHANNEL_ID}>. 🛡️ The role will be removed in one hour.")

            await asyncio.sleep(3600)

            if role in user.roles:
                await user.remove_roles(role)
                await ctx.send(f"Role removed from {user.mention} after the time expired! ⏳")
                await logs_channel.send(f"{user.mention} had the role removed after one hour. ⏳")
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
        print(f"Error in shield command: {e}")

bot.run('MTI3ODEzMzc1OTUzOTAyMzkzMw.GKlPLI.1kc6PK9nAJdYbalTpTwoJ-jOriM4b1RZf6do6Y')
