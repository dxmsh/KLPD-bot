import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import requests
from datetime import datetime, timedelta

LEVEL_ROLES = {
    5: '1277827840779223103',
    10: '770052498152751124',
    15: '770052789832908820',
    20: '770053114458800159',
    25: '770053656241504296',
    30: '770053995003248660',
    35: '770054205577625640',
    40: '770054327854301194',
    45: '787445586890195015',
    50: '787445311055855626',
    55: '787445340647194624',
    60: '787445367775166474',
    65: '816202626588213258',
    70: '816202958697791488',
    75: '820788399568060426'
}

class Levelling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = self.load_data()
        self.daily_reset.start()

    async def prepare(self):
        await self.bot.tree.sync()
        print("Bot tree synced.")

    @commands.Cog.listener()
    async def on_ready(self):
        #await self.bot.tree.sync()
        print("levels.py loaded.")

    def load_data(self):
        try:
            with open('users.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_data(self):
        with open('users.json', 'w') as f:
            json.dump(self.user_data, f, indent=4)

    async def assign_role(self, member, level):
        guild = member.guild
        for lvl, role_id in LEVEL_ROLES.items():
            role = guild.get_role(int(role_id))
            if role:
                if level >= lvl:
                    if role not in member.roles:
                        await member.add_roles(role)
                        await member.send(f"You have been assigned the role: {role.name}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        if user_id not in self.user_data:
            self.user_data[user_id] = {'level': 1, 'xp': 0, 'last_daily': None}

        self.user_data[user_id]['xp'] += 10  # Add XP for each message
        xp = self.user_data[user_id]['xp']
        level = self.user_data[user_id]['level']

        if xp >= level * 100:
            self.user_data[user_id]['level'] += 1
            self.user_data[user_id]['xp'] = 0
            await message.channel.send(f"Congratulations {message.author.mention}, you leveled up to {level + 1}!")
            await self.assign_role(message.author, level + 1)

        self.save_data()

    @app_commands.command(name="level", description="Check your level and XP")
    async def level(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member if member else interaction.user
        user_id = str(member.id) if member else str(interaction.user.id)
        if user_id not in self.user_data:
            await interaction.response.send_message("User data not found.")
            return

        level = self.user_data[user_id]['level']
        xp = self.user_data[user_id]['xp']
        xpforlevelup = (level*100)-xp
        embed = discord.Embed(title="Level", color=0x00ff00)
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="XP", value=xp, inline=True)
        embed.add_field(name="XP for Level Up", value=xpforlevelup, inline=True)
        embed.set_footer(text=f"{member.name}", icon_url=member.avatar.url)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the top 10 users by level")
    async def leaderboard(self, interaction: discord.Interaction):
        with open('users.json', 'r') as f:
            data = json.load(f)

        top_users = {k: v for k, v in sorted(data.items(), key=lambda item: item[1]['level'], reverse=True)}

        leaderboard_text = ""
        for position, (user_id, user_info) in enumerate(top_users.items()):
            member = self.bot.get_user(int(user_id))
            if member:
                leaderboard_text += f"{position + 1}. {member.mention} - Level {user_info['level']}\n"

        embed = discord.Embed(title="Leaderboard", description=leaderboard_text, color=0xffd700)
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="daily", description="Collect your daily XP")
    async def daily(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        now = datetime.utcnow()
        if user_id not in self.user_data:
            self.user_data[user_id] = {'level': 1, 'xp': 0, 'last_daily': None}

        last_daily = self.user_data[user_id]['last_daily']
        if last_daily and datetime.fromisoformat(last_daily) > now - timedelta(days=1):
            await interaction.response.send_message("You have already collected your daily XP. Try again later.", ephemeral=True)
            return

        self.user_data[user_id]['xp'] += 50  # Daily XP reward
        self.user_data[user_id]['last_daily'] = now.isoformat()
        self.save_data()
        await interaction.response.send_message("You have collected your daily 50 XP!")

    @tasks.loop(hours=24)
    async def daily_reset(self):
        now = datetime.utcnow()
        for user_id in self.user_data:
            self.user_data[user_id]['last_daily'] = None
        self.save_data()

    @daily_reset.before_loop
    async def before_daily_reset(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    cog = Levelling(bot)
    await bot.add_cog(cog)
    #await cog.prepare()
