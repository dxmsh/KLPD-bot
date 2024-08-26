import discord
from discord.ext import commands
from discord import app_commands
import json
import random

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

    @app_commands.command(name="userinfo", description="View information on yourself or another user.")
    async def info(self, interaction: discord.Interaction, member: discord.Member = None):
        member = interaction.user if not member else member
        roles = [role for role in member.roles if role.name != "@everyone"]
        embed = discord.Embed(colour=member.color,
                            timestamp=interaction.created_at)
        embed.set_author(name=f"User Info - {member.name}")
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(
            text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.add_field(name="ID:", value=member.id)
        embed.add_field(name="Guild Name:", value=f'{member.display_name}')
        embed.add_field(name="Created at:",
                        value=member.created_at.strftime("%m/%d/%Y, %H:%M UTC"))
        embed.add_field(name="Joined at:",
                        value=member.joined_at.strftime("%m/%d/%Y, %H:%M UTC"))
        embed.add_field(name=f"Roles ({len(roles)})", value=" ".join(
            [role.mention for role in roles]))
        embed.add_field(name="Top Role:", value=member.top_role.mention)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question.")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Yes.",
            "No.",
            "Maybe.",
            "Definitely not.",
            "Absolutely!",
            "I'm not sure, try again later.",
            "Probably.",
            "I don't think so.",
            "Yes, but only if you try harder.",
            "No way.",
            "Ask again later.",
            "Yes, but don't count on it.",
            "Most likely.",
            "I wouldn't count on it.",
            "Yes, but it's uncertain."
        ]
        response = random.choice(responses)
        await interaction.response.send_message(f"**Question:** {question}\n**Answer:** {response}")

async def setup(bot):
    await bot.add_cog(commands(bot))
