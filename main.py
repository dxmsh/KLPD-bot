import discord
from discord.ext import commands
from discord import app_commands
import json
from dotenv import load_dotenv
import os
import socket
import time

with open('config.json', 'r') as f:
    config = json.load(f)
load_dotenv()

PREFIX = config['prefix']
DEV_IDS = config['devID']
GUILD_IDS = [int(guild_id) for guild_id in config['guildID']]

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

@bot.event
async def on_ready():
    for guild in GUILD_IDS:
        guild = discord.Object(guild)
        await bot.tree.sync(guild=guild)
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

@bot.tree.command(name="ping", description="Check the bot's latency.")
async def slash_command(interaction:discord.Interaction):
    try:
        latency = bot.latency
        latency_ms = round(latency * 1000)
        await interaction.response.send_message(f"> :ping_pong: My ping is **{latency_ms}** ms")
    except Exception as e:
        print(f"Error in ping command: {e}")

@bot.tree.command(name="rping", description="Ping a remote host.")
async def slash_command(interaction:discord.Interaction, host: str, port: int):
        try:
            start_time = time.time()
            with socket.create_connection((host, port), timeout=5) as sock:
                latency = (time.time()-start_time)*1000
            embed = discord.Embed(
                title = ":ping_pong: Remote Ping",
                description="Ping Results",
                color=discord.Color.green()
            )
            embed.add_field(
                name = "Host",
                value = f"{host}",
                inline = False
            )
            embed.add_field(
                name = "Port",
                value = f"{port}",
                inline = False
            )
            embed.add_field(
                name = "Ping",
                value = f"{round(latency, 2)} ms",
                inline = False
            )
            embed.set_footer(
                text = f"Requested by {interaction.user.name}",
                icon_url = interaction.user.avatar
            )
            await interaction.response.send_message(embed=embed)
        except (socket.timeout, socket.gaierror, ConnectionRefusedError) as e:
            embed = discord.Embed(
                title = ":ping_pong: Remote Ping",
                description="Ping Error",
                color=discord.Color.red()
            )
            embed.add_field(
                name = "Host",
                value = f"{host}",
                inline = False
            )
            embed.add_field(
                name = "Port",
                value = f"{port}",
                inline = False
            )
            embed.add_field(
                name = "Result",
                value = e,
                inline = False
            )
            embed.set_footer(
                text = f"Requested by {interaction.user.name}",
                icon_url = interaction.user.avatar
            )
            await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="View yours, or someone else's avatar.")
async def slash_command(interaction:discord.Interaction, mention: discord.User | None):
    if mention is not None:
        await interaction.response.send_message(mention.avatar)
    else:
        await interaction.response.send_message(interaction.user.avatar)

bot.run(os.getenv('BOT_TOKEN'))
