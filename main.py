import discord
from discord.ext import commands, tasks
from datetime import datetime
import time

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

role_name = 'SCRIPT DETECTED ✅'
channel_name = '10 hour outcast casino'
timeout_duration = 10 * 60 * 60  # 10 ساعات بالثواني

# Create embed function
def create_embed(executor, target, response, time_diff):
    embed = discord.Embed(
        title="Rob Detection",
        description="**Script Detection Report**",
        color=discord.Color.red()
    )
    embed.add_field(name="Executor", value=executor.mention, inline=False)
    embed.add_field(name="Target", value=target.mention, inline=False)
    embed.add_field(name="Time Difference", value=f"{time_diff:.6f} seconds", inline=False)
    embed.add_field(name="Script Detected", value=response, inline=False)
    embed.set_footer(text=f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    return embed

# Command to detect script
@bot.command()
async def rob(ctx, member: discord.Member):
    last_message = ctx.message
    executor = ctx.author

    # Check the last message of the target
    async for message in ctx.channel.history(limit=10):
        if message.author == member:
            target_last_message = message
            break
    else:
        await ctx.send(f"No recent messages found for {member.mention}")
        return

    # Compare time differences
    time_diff = (last_message.created_at - target_last_message.created_at).total_seconds()

    # Check if it's a script or human
    if time_diff <= 1:
        response = "✅ SCRIPT DETECTED ✅"
        # Assign the role
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            role = await ctx.guild.create_role(name=role_name, permissions=discord.Permissions.none())
        await member.add_roles(role)

        # Create restricted channel if not exists
        restricted_channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
        if restricted_channel is None:
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                role: discord.PermissionOverwrite(view_channel=True)
            }
            restricted_channel = await ctx.guild.create_text_channel(channel_name, overwrites=overwrites)

        # Send a message to the user
        try:
            await member.send(f"You have been restricted for 10 hours due to script detection.")
        except discord.Forbidden:
            pass

        # Start timeout task
        await remove_role_after_timeout(member, role, restricted_channel)
    else:
        response = "❌ SCRIPT DETECTED ❌"

    # Create and send embed
    embed = create_embed(executor, member, response, time_diff)
    log_channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
    if log_channel:
        await log_channel.send(embed=embed)

# Remove the role after the timeout
async def remove_role_after_timeout(member, role, restricted_channel):
    await discord.utils.sleep_until(datetime.utcnow().timestamp() + timeout_duration)
    await member.remove_roles(role)
    await member.send(f"Your restriction has been lifted.")
    
    # If no one else has the role, remove the channel
    role_members = [m for m in restricted_channel.guild.members if role in m.roles]
    if not role_members:
        await restricted_channel.delete()

# Command to remove the restriction manually
@bot.command()
async def done(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if role in member.roles:
        await member.remove_roles(role)
        await member.send("Your restriction has been manually lifted.")
    else:
        await ctx.send(f"{member.mention} does not have the {role_name} role.")

# Run the bot
bot.run('MTI3ODEzMzc1OTUzOTAyMzkzMw.GQbBko.0r4t9KwKeYLVpxQo2yOoHuloB3KYlNbhxDBJdE')
