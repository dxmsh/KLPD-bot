import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio

with open('config.json', 'r') as f:
    config = json.load(f)

DEV_IDS = [int(id) for id in config['devID']]
WARN_FILE = 'warns.json'

class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def prepare(self):
        #await self.bot.tree.sync()
        print("Bot tree synced.")

    @commands.Cog.listener()
    async def on_ready(self):
        # await self.bot.tree.sync()
        print("moderation.py loaded.")

    @app_commands.command(name="warn", description="Warn a user.")
    @app_commands.describe(member="The person to warn.")
    @app_commands.describe(reason="Reason for warning.")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if os.path.exists(WARN_FILE):
            try:
                with open(WARN_FILE, 'r') as warnfileread:
                    warns = json.load(warnfileread)
                    print("log 4")
            except json.JSONDecodeError:
                print("Error: JSON decode error. The file might be corrupted or not properly formatted.")
                warns = {}
            except IOError as e:
                print(f"Error: IOError while reading file - {e}")
                warns = {}
        else:
            print("warns.json does not exist. Creating a new file.")
            try:
                with open(WARN_FILE, 'w') as warnfilewrite:
                    json.dump({}, warnfilewrite, indent=4)
                print("warns.json created successfully.")
                warns = {}
            except IOError as e:
                print(f"Error: IOError while creating file - {e}")
                warns = {}

        user_id = str(member.id)
        if user_id in warns:
            warns[user_id]['warnings'] += 1
            warns[user_id]['reasons'].append(reason)
            warns[user_id]['moderators'].append(str(interaction.user))
        else:
            warns[user_id] = {
                'user': str(member),
                'warnings': 1,
                'reasons': [reason],
                'moderators': [str(interaction.user)]
            }

        try:
            with open(WARN_FILE, 'w') as warnfilewrite:
                json.dump(warns, warnfilewrite, indent=4)
        except IOError as e:
            await interaction.response.send_message(f"Error: IOError while writing to file - {e}", ephemeral=True)
            return

        embed = discord.Embed(
            title="Warning issued!",
            color=discord.Color.red()
        )
        embed.add_field(name="Warned User:", value=f"{member.mention}", inline=False)
        embed.add_field(name="Reason:", value=reason, inline=False)
        embed.set_footer(text=f"Warned by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="warnings", description="View the warnings of a user.")
    @app_commands.describe(member="The user whose warnings you want to view.")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        if os.path.exists(WARN_FILE):
            try:
                with open(WARN_FILE, 'r') as warnfileread:
                    warns = json.load(warnfileread)
            except json.JSONDecodeError:
                await interaction.response.send_message("Error: JSON decode error. The file might be corrupted or not properly formatted.", ephemeral=True)
                return
            except IOError as e:
                await interaction.response.send_message(f"Error: IOError while reading file - {e}", ephemeral=True)
                return
        else:
            await interaction.response.send_message("No warnings have been recorded yet.", ephemeral=True)
            return

        user_id = str(member.id)
        if user_id in warns:
            user_warnings = warns[user_id]
            embed = discord.Embed(
                title="Warnings",
                description=f"Warnings for {member.mention}",
                color=discord.Color.red()
            )
            embed.add_field(name="Total Warnings:", value=user_warnings['warnings'], inline=False)
            reasons_with_moderators = "\n".join(
                f"{reason} (by {moderator})" for reason, moderator in zip(user_warnings['reasons'], user_warnings['moderators'])
            )
            embed.add_field(name="Reasons:", value=reasons_with_moderators if reasons_with_moderators else "No reasons recorded.", inline=False)
            embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url)
            embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"{member.mention} has no warnings recorded.", ephemeral=True)

async def setup(bot):
    cog = moderation(bot)
    await bot.add_cog(cog)
    # await cog.prepare()
