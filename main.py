import discord
import jishaku
from discord.ext import commands, tasks
from discord import app_commands
import json
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timedelta, timezone
from mcstatus.server import JavaServer

with open('config.json', 'r') as f:
    config = json.load(f)
load_dotenv()

PREFIX = config['prefix']

SERVER_IP = '157.90.3.16'
SERVER_PORT = 40165
CHANNEL_ID = 1278337388590137345

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

@tasks.loop(seconds=120)
async def check_status():
    guild_id = 493063429129502720
    role_id = 771808654805958657
    channel_id = 1278339197878669446

    guild = bot.get_guild(guild_id)
    role = discord.utils.get(guild.roles, id=role_id)
    channel = bot.get_channel(channel_id)
    count = 0
    if role:
        for member in guild.members:
            if member.status != discord.Status.offline:
                count = count + 1
                has_custom_activity = False

                for activity in member.activities:
                    if isinstance(activity, discord.CustomActivity) and "gg/klpd" in activity.name:
                        has_custom_activity = True
                        break

                if has_custom_activity:
                    if role not in member.roles:
                        await member.add_roles(role)
                        await channel.send(f":information_source: Assigned {role.name} to {member.name}")
                        await member.send(f"You were given the **Sexy as Fuck** role in KLPD.")
                else:
                    if role in member.roles:
                        await member.remove_roles(role)
                        await channel.send(f":information_source: Removed {role.name} from {member.name}")
                        await member.send(f"You were removed from the **Sexy as Fuck** role in KLPD.")
        await channel.send(f":white_check_mark: Finished checking {count} members.")
@bot.event
async def on_ready():
    await load()
    check_status.start()
    update_channel_name.start()
    print("---------READY---------")
    print(f"Logged in as: {bot.user.name}")
    print("-----------------------")

@tasks.loop(minutes=1)  # Repeat every minute
async def update_channel_name():
    log_channel_id = 1278340225512243291
    log_channel = bot.get_channel(log_channel_id)
    try:
        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
        status = server.status()

        channel = bot.get_channel(CHANNEL_ID)
        if channel and isinstance(channel, discord.VoiceChannel):
            await channel.edit(name=f"🟢 Players: {status.players.online}/{status.players.max}")
            await log_channel.send(f":white_check_mark: Updated player count to {status.players.online}/{status.players.max}")
    except Exception as e:
        await log_channel.send(f":x: <@772336857970114590> Failed to retrieve server status or update channel: {e}")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        try:
            await message.channel.send(f"> My prefix is **{PREFIX}**")
        except Exception as e:
            print(f"Error in bot mention: {e}")

    await bot.process_commands(message)

async def load():
    print("Loading cogs...")
    await bot.load_extension('jishaku')
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            print(f"Loading {filename}...")
            await bot.load_extension(f"cogs.{filename[:-3]}")
    print("Syncing command tree...")
    await bot.tree.sync()

async def main():
    async with bot:
        await bot.start(os.getenv('BOT_TOKEN'))

asyncio.run(main())
