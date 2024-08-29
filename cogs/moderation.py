import discord
from discord.ext import commands
from discord import app_commands, utils
import os
import json
import asyncio
from typing import Optional
from humanfriendly import parse_timespan, InvalidTimespan
from datetime import timedelta, datetime

with open('config.json', 'r') as f:
    config = json.load(f)

DEV_IDS = [int(id) for id in config['devID']]
WARN_FILE = 'warns.json'

mod_channel_id = 1278379703589404732

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

        mod_channel = self.bot.get_channel(mod_channel_id)
        if os.path.exists(WARN_FILE):
            try:
                with open(WARN_FILE, 'r') as warnfileread:
                    warns = json.load(warnfileread)
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
        await mod_channel.send(embed=embed)
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


    @app_commands.command(name="kick", description="kick a user.")
    @app_commands.describe(member="The person to kick.")
    @app_commands.describe(reason="Reason for kick.")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        mod_channel = self.bot.get_channel(mod_channel_id)
        user_id = str(member.id)
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="User Kicked!",
            color=discord.Color.red()
        )
        embed.add_field(name="Kicked User:", value=f"{member.mention}", inline=False)
        embed.add_field(name="Reason:", value=reason, inline=False)
        embed.set_footer(text=f"Kicked by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
        await mod_channel.send(embed=embed)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Ban a user.")
    @app_commands.describe(member="The person to ban.")
    @app_commands.describe(reason="Reason for ban.")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        mod_channel = self.bot.get_channel(mod_channel_id)
        user_id = str(member.id)
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="User Banned!",
            color=discord.Color.red()
        )
        embed.add_field(name="Banned User:", value=f"{member.mention}", inline=False)
        embed.add_field(name="Reason:", value=reason, inline=False)
        embed.set_footer(text=f"Banned by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
        await mod_channel.send(embed=embed)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unban", description="Unban a user.")
    @app_commands.describe(user="The person to unban.")
    @app_commands.describe(reason="Reason for unban.")
    async def unban(self, interaction: discord.Interaction, user: discord.User, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        mod_channel = self.bot.get_channel(mod_channel_id)
        assert interaction.guild is not None
        try:
            await interaction.guild.fetch_ban(user)
        except:
            await interaction.response.send_message(f"{user} is not banned from this server.")
            return
        else:
                await interaction.guild.unban(user, reason=reason)
                embed = discord.Embed(
                title="User Unbanned!",
                color=discord.Color.red()
                )
                embed.add_field(name="Unbanned User:", value=f"{user.mention}", inline=False)
                embed.add_field(name="Reason:", value=reason, inline=False)
                embed.set_footer(text=f"Unbanned by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
                await mod_channel.send(embed=embed)
                await interaction.response.send_message(embed=embed)

    @app_commands.command(name="mute", description="Mutes a member.")
    async def   mute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", duration: str = '1h'):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        real_duration = duration
        mod_channel = self.bot.get_channel(mod_channel_id)
        try:
            duration = parse_timespan(duration)
        except:
            return await interaction.response.send_message("Invalid duration (e.g. 1m, 1h, 1d)", ephemeral=True)

        await member.timeout(utils.utcnow() + timedelta(seconds=duration), reason=reason)
        embed = discord.Embed(
            title="User Muted!",
            color=discord.Color.green()
        )
        embed.add_field(name="Muted User:", value=f"{member.mention}", inline=False)
        embed.add_field(name="Reason:", value=reason, inline=False)
        embed.add_field(name="Duration:", value=real_duration, inline=False)
        embed.set_footer(text=f"Muted by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
        await mod_channel.send(embed=embed)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="unmute", description="Unmutes a member.")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        mod_channel = self.bot.get_channel(mod_channel_id)
        if not member.is_timed_out():
            return await interaction.response.send_message(f"{member.name} is not muted.", ephemeral=True)

        await member.timeout(None, reason=reason)
        embed = discord.Embed(
            title="User Unmuted!",
            color=discord.Color.green()
        )
        embed.add_field(name="Unmuted User:", value=f"{member.mention}", inline=False)
        embed.add_field(name="Reason:", value=reason, inline=False)
        embed.set_footer(text=f"Unmuted by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
        await mod_channel.send(embed=embed)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="purge", description="Purge messages in the channel.")
    async def purge(self, interaction: discord.Interaction, amount: int, reason: str = "No reason provided."):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if amount > 200:
            await interaction.response.send_message("You can purge a maximum of 200 messages at once.", ephemeral=True)

        await interaction.channel.purge(limit=amount, reason=reason)
        mod_channel = self.bot.get_channel(mod_channel_id)
        embed = discord.Embed(
            title="Channnel Purged!",
            color=discord.Color.red()
        )
        embed.add_field(name="Number of Messages:", value=f"{amount}", inline=False)
        embed.add_field(name="Channel", value=interaction.channel.name, inline=False)
        embed.add_field(name="Reason:", value=reason, inline=False)
        embed.set_footer(text=f"Purged by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/443051446942957568/9dee701c40f36b64b6e11f8dfeb110f9.png?size=1024")
        await mod_channel.send(embed=embed)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    cog = moderation(bot)
    await bot.add_cog(cog)
    # await cog.prepare()
