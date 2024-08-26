import discord
from discord.ext import commands
from discord import app_commands
import json

with open('config.json', 'r') as f:
    config = json.load(f)

PREFIX = config['prefix']
DEV_IDS = config['devID']

class commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print("commands.py loaded.")

    @app_commands.command(name="ping", description="Check the bot's latency.")
    async def ping(self, interaction: discord.Interaction):
        try:
            latency = self.bot.latency
            latency_ms = round(latency * 1000)
            await interaction.response.send_message(f"> :ping_pong: My ping is **{latency_ms}** ms")
        except Exception as e:
            print(f"Error in ping command: {e}")

    @app_commands.command(name="avatar", description="View yours, or someone else's avatar.")
    async def avatar(self, interaction:discord.Interaction, mention: discord.User | None):
        if mention is not None:
            await interaction.response.send_message(mention.avatar)
        else:
            await interaction.response.send_message(interaction.user.avatar)

    @app_commands.command(name="devs", description="List the current bot devs.")
    async def slash_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="KLPD",
            color=discord.Color.red()
            )
        devs_list = "\n".join([f"<@{dev}>" for dev in DEV_IDS])
        embed.add_field(name="Developers:", value=devs_list, inline=False)
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(commands(bot))
