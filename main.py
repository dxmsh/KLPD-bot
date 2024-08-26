import discord
import jishaku
from discord.ext import commands
from discord import app_commands
import json
from dotenv import load_dotenv
import os
import asyncio

with open('config.json', 'r') as f:
    config = json.load(f)
load_dotenv()

PREFIX = config['prefix']

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

@bot.event
async def on_ready():
    print("---------READY---------")
    print(f"Logged in as: {bot.user.name}")
    print("-----------------------")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        try:
            await message.channel.send(f"> My prefix is **{PREFIX}**")
        except Exception as e:
            print(f"Error in bot mention: {e}")

    await bot.process_commands(message)

async def load():
    await bot.load_extension('jishaku')
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            print(f"Loading {filename}...")
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await load()
        await bot.start(os.getenv('BOT_TOKEN'))

asyncio.run(main())
