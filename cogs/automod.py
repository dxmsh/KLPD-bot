import discord
from discord.ext import commands
import os
import json
import re

with open('config.json', 'r') as f:
    config = json.load(f)
DEV_IDS = [int(id) for id in config['devID']]

class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.author.guild_permissions.administrator:
            return

        invite_pattern = r"(?:https?://)?discord(?:app)?\.gg/([a-zA-Z0-9\-]+)"
        match = re.search(invite_pattern, message.content)
        if match:
            invite_code = match.group(1)
            if invite_code != "klpd":
                await message.delete()
                warning_message = f"{message.author.mention}, you are not allowed to post invite links."
                await message.channel.send(warning_message)

async def setup(bot):
    await bot.add_cog(Automod(bot))
