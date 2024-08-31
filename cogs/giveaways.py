import discord
from discord.ext import commands, tasks
import asyncio
import random
import datetime
import json
import os
import re
from math import ceil
from discord import Embed, SelectOption, Interaction
from discord.ui import Select, View, Modal, TextInput

# Helper functions and data
active_giveaways = {}

def load_giveaway_settings():
    if os.path.exists("giveaway_settings.json"):
        with open("giveaway_settings.json", "r") as f:
            return json.load(f)
    return {}

def save_giveaway_settings(settings):
    with open("giveaway_settings.json", "w") as f:
        json.dump(settings, f)

def save_giveaways():
    data = {k: v.to_dict() for k, v in active_giveaways.items()}
    with open("giveaways.json", "w") as f:
        json.dump(data, f)

def load_giveaways():
    if os.path.exists("giveaways.json"):
        with open("giveaways.json", "r") as f:
            data = json.load(f)
        return {k: Giveaway.from_dict(v) for k, v in data.items()}
    return {}

async def get_role(interaction, role_input):
    try:
        role = interaction.guild.get_role(int(role_input))
        if role:
            return role
    except ValueError:
        pass
    role = discord.utils.get(interaction.guild.roles, name=role_input)
    return role

giveaway_settings = load_giveaway_settings()

class GiveawaysCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=3)
    async def check_giveaways(self):
        current_time = datetime.datetime.now().timestamp()
        ended_giveaways = [gid for gid, g in active_giveaways.items() if current_time >= g.end_time and not g.ended]
        for giveaway_id in ended_giveaways:
            await self.end_giveaway(giveaway_id)

    async def end_giveaway(self, giveaway_id):
        giveaway = active_giveaways.get(giveaway_id)
        if not giveaway or giveaway.ended:
            return
        channel = self.bot.get_channel(giveaway.channel_id)
        if not channel:
            return
        giveaway.ended = True
        save_giveaways()

        try:
            message = await channel.fetch_message(giveaway.message_id)
            if not giveaway.participants:
                embed = discord.Embed(title="🎉 Giveaway Ended!", color=0xff0000)
                embed.description = f"The giveaway for **{giveaway.prize}** has ended, but no one participated. 😢"
            else:
                winners = random.sample(list(giveaway.participants), min(giveaway.winners, len(giveaway.participants)))
                winner_mentions = [f"<@{winner}>" for winner in winners]
                embed = discord.Embed(title="🎉 Giveaway Ended! 🎉", color=0x00ff00)
                embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/CX8j8C2jGASw8HGroq0vIMrT4KwyzZVMoybKMDritFc/https/cdn.discordapp.com/icons/493063429129502720/a_152d897749da45e310f195129b41aff0.gif")
                embed.add_field(name="Prize", value=giveaway.prize, inline=False)
                embed.add_field(name="Winners", value="\n".join(winner_mentions), inline=False)
                win_str = f"Congratulations, {', '.join(winner_mentions)}! You've won the giveaway for **{giveaway.prize}**!"
            embed.set_footer(text=f"Hosted by {message.guild.get_member(giveaway.host_id).display_name}", icon_url=message.guild.get_member(giveaway.host_id).avatar.url)
            view = GiveawayView(giveaway_id)
            for item in view.children:
                item.disabled = True
            await message.edit(embed=embed, view=view)
            await message.channel.send(win_str)
        except discord.errors.NotFound:
            print(f"Giveaway message {giveaway.message_id} not found. It may have been deleted.")
        except Exception as e:
            print(f"Error updating giveaway message: {e}")

    @commands.hybrid_command(name="giveaway", description="Start a new giveaway")
    @commands.has_permissions(manage_messages=True)
    async def giveaway(self, ctx, channel: discord.TextChannel):
        modal = GiveawayModal(ctx, channel)
        await ctx.interaction.response.send_modal(modal)

    @commands.hybrid_command(name="reroll", description="Reroll the winner(s) of the last giveaway")
    @commands.has_permissions(manage_messages=True)
    async def reroll(self, ctx):
        channel_giveaways = [g for g in active_giveaways.values() if g.channel_id == ctx.channel.id and g.ended]
        if not channel_giveaways:
            await ctx.send("There are no ended giveaways to reroll in this channel.")
            return
        giveaway = max(channel_giveaways, key=lambda g: g.end_time)
        if not giveaway.participants:
            await ctx.send("No one participated in the giveaway. 😢")
            return
        new_winners = random.sample(list(giveaway.participants), min(giveaway.winners, len(giveaway.participants)))
        winner_mentions = [f"<@{winner}>" for winner in new_winners]
        embed = discord.Embed(title="🎉 Giveaway Rerolled! 🎉", color=0xff00ff)
        embed.add_field(name="Prize", value=giveaway.prize, inline=False)
        embed.add_field(name="New Winner", value="\n".join(winner_mentions), inline=False)
        embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/CX8j8C2jGASw8HGroq0vIMrT4KwyzZVMoybKMDritFc/https/cdn.discordapp.com/icons/493063429129502720/a_152d897749da45e310f195129b41aff0.gif")
        host = ctx.guild.get_member(giveaway.host_id)
        embed.set_footer(text=f"Hosted by <@{host.name}>")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="cancel", description="Cancel the current giveaway")
    @commands.has_permissions(manage_messages=True)
    async def cancel(self, ctx):
        channel_giveaways = [gid for gid, g in active_giveaways.items() if g.channel_id == ctx.channel.id and not g.ended]
        if not channel_giveaways:
            await ctx.send("There's no active giveaway to cancel in this channel.")
            return
        giveaway_id = channel_giveaways[0]
        giveaway = active_giveaways[giveaway_id]
        del active_giveaways[giveaway_id]
        save_giveaways()
        embed = discord.Embed(title="🚫 Giveaway Cancelled 🚫", color=0xff0000)
        embed.add_field(name="Prize", value=giveaway.prize, inline=False)
        embed.set_footer(text=f"Cancelled by {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="list", description="List all active giveaways")
    async def list_giveaways(self, ctx):
        active = [g for g in active_giveaways.values() if not g.ended]
        if not active:
            await ctx.send("There are no active giveaways at the moment.")
            return
        embed = discord.Embed(title="Active Giveaways", color=0x00ff00)
        for giveaway in active:
            channel = self.bot.get_channel(giveaway.channel_id)
            embed.add_field(
                name=f"Giveaway in {channel.name}",
                value=f"Prize: {giveaway.prize}\nWinners: {giveaway.winners}\nEntries: {len(giveaway.participants)}\nEnds: <t:{int(giveaway.end_time)}:R>",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="giveaway_settings", description="Update giveaway embed settings")
    @commands.has_permissions(manage_messages=True)
    async def giveaway_settings_command(self, ctx):
        embed = create_settings_embed(ctx.guild)
        view = GiveawaySettingsView(ctx)
        await ctx.send(embed=embed, view=view)

class Giveaway:
    def __init__(self, channel_id, prize, duration, host_id, winners=1, role_requirement=None, notes=None, message_id=None, end_time=None, status_requirement=False):
        self.channel_id = channel_id
        self.prize = prize
        self.duration = max(duration, 60)  # Ensure minimum duration of 1 minute
        self.host_id = host_id
        self.winners = winners
        self.role_requirement = role_requirement.id if isinstance(role_requirement, discord.Role) else role_requirement
        self.notes = notes or ""
        self.participants = set()
        self.message_id = message_id
        self.end_time = end_time or (datetime.datetime.now() + datetime.timedelta(seconds=self.duration)).timestamp()
        self.ended = False
        self.status_requirement = status_requirement

    def to_dict(self):
        return {
            "channel_id": self.channel_id,
            "prize": self.prize,
            "duration": self.duration,
            "host_id": self.host_id,
            "winners": self.winners,
            "role_requirement": self.role_requirement,  # Store role ID
            "notes": self.notes,
            "participants": list(self.participants),
            "message_id": self.message_id,
            "end_time": self.end_time,
            "ended": self.ended,
            "status_requirement": self.status_requirement
        }

    @classmethod
    def from_dict(cls, data):
        giveaway = cls(
            data["channel_id"],
            data["prize"],
            data["duration"],
            data["host_id"],
            data["winners"],
            data["role_requirement"],  # This will be the role ID
            data["notes"],
            data["message_id"],
            data["end_time"],
            data.get("status_requirement", False)
        )
        giveaway.participants = set(data["participants"])
        giveaway.ended = data["ended"]
        return giveaway

class GiveawayModal(discord.ui.Modal, title="Create a Giveaway"):
    prize = discord.ui.TextInput(label="Prize", placeholder="Enter the giveaway prize")
    duration = discord.ui.TextInput(label="Duration", placeholder="Enter the duration (e.g., 1h 30m, 2d)")
    winners = discord.ui.TextInput(label="Number of Winners", placeholder="Enter the number of winners")
    notes = discord.ui.TextInput(label="Notes (optional)", placeholder="Enter any additional notes", style=discord.TextStyle.long, required=False)

    def __init__(self, ctx, channel):
        super().__init__()
        self.ctx = ctx
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            duration_seconds = max(parse_duration(self.duration.value), 60)  # Ensure minimum duration of 1 minute
            winners = int(self.winners.value)

            if winners <= 0:
                raise ValueError("Number of winners must be positive")

            # Store the giveaway data temporarily
            interaction.client.temp_giveaway_data = {
                "prize": self.prize.value,
                "duration": duration_seconds,
                "winners": winners,
                "notes": self.notes.value,
                "channel_id": self.channel.id,
                "host_id": interaction.user.id,
                "status_requirement": False
            }

            # Create a select menu for requirements
            select = discord.ui.Select(
                placeholder="Add requirements?",  # Updated placeholder
                options=[
                    discord.SelectOption(label="No requirement", value="none"),
                    discord.SelectOption(label="Role requirement", value="role"),
                    discord.SelectOption(label="Status requirement", value="status")
                ]
            )

            async def select_callback(interaction: discord.Interaction):
                if select.values[0] == "none":
                    await update_confirmation_message(interaction, None)
                elif select.values[0] == "role":
                    await interaction.response.send_modal(RoleRequirementModal())
                elif select.values[0] == "status":
                    interaction.client.temp_giveaway_data["status_requirement"] = True
                    await update_confirmation_message(interaction, None)

            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)

            # Create and send the initial confirmation message
            embed = create_confirmation_embed(interaction.client.temp_giveaway_data, None)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(f"Invalid input: {str(e)}. Giveaway creation cancelled.", ephemeral=True)

class RoleRequirementModal(discord.ui.Modal, title="Role Requirement"):
    role = discord.ui.TextInput(label="Role", placeholder="Enter role name or ID")

    async def on_submit(self, interaction: discord.Interaction):
        role_requirement = await get_role(interaction, self.role.value)
        if role_requirement:
            await update_confirmation_message(interaction, role_requirement)
        else:
            await interaction.response.send_message("Couldn't find the specified role. Please try again.", ephemeral=True)

async def resolve_role(guild, role_id):
    return guild.get_role(role_id)

async def get_server(interaction, server_id):
    try:
        # Convert the server ID to an integer
        server_id = int(server_id)
    except ValueError:
        # Return None if the server ID is not a valid integer
        return None, None

    # Get the server (guild) object by ID
    server = interaction.client.get_guild(server_id)

    if server:
        # Try to create an invite link to the server
        try:
            # Get the first available text channel
            channel = next((ch for ch in server.channels if isinstance(ch, discord.TextChannel)), None)
            if channel:
                invite = await channel.create_invite(max_age=0, max_uses=0, unique=True)
                return server.id, str(invite)
        except discord.errors.Forbidden:
            # If the bot doesn't have permissions to create an invite, return the server but without an invite link
            return server.id, None

    # Return None if the server was not found or if the bot couldn't create an invite
    return None, None


class ServerRequirementModal(discord.ui.Modal, title="Server Requirement"):
    server = discord.ui.TextInput(label="Server ID", placeholder="Enter server ID")

    async def on_submit(self, interaction: discord.Interaction):
        server_requirement, server_invite = await get_server(interaction, self.server.value)
        if server_requirement:
            interaction.client.temp_giveaway_data["server_invite"] = server_invite
            await update_confirmation_message(interaction, None, server_requirement, None)  # Added None for entry_limit
        else:
            await interaction.response.send_message("I'm not in the specified server or couldn't create an invite. Please try again.", ephemeral=True)

class EntryLimitModal(discord.ui.Modal, title="Entry Limit"):
    limit = discord.ui.TextInput(label="Entry Limit", placeholder="Enter the maximum number of entries")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            entry_limit = int(self.limit.value)
            if entry_limit <= 0:
                raise ValueError("Entry limit must be a positive number.")
            await update_confirmation_message(interaction, None, None, entry_limit)
        except ValueError as e:
            await interaction.response.send_message(f"Invalid input: {e}", ephemeral=True)

class GiveawaySettingsView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.add_item(self.image_select())
        self.add_item(self.thumbnail_select())
        self.add_item(self.color_select())
        self.add_item(self.emoji_button())
        self.add_item(self.footer_button())

    def image_select(self):
        select = Select(
            placeholder="Select image option",
            options=[
                SelectOption(label="Default", value="default"),
                SelectOption(label="Custom", value="custom"),
            ]
        )
        select.callback = self.image_callback
        return select

    def thumbnail_select(self):
        select = Select(
            placeholder="Select thumbnail option",
            options=[
                SelectOption(label="Default", value="default"),
                SelectOption(label="Custom", value="custom"),
            ]
        )
        select.callback = self.thumbnail_callback
        return select

    def color_select(self):
        select = Select(
            placeholder="Select color scheme",
            options=[
                SelectOption(label="Default", value="default"),
                SelectOption(label="Custom", value="custom"),
            ]
        )
        select.callback = self.color_callback
        return select

    def emoji_button(self):
        button = discord.ui.Button(label="Set Custom Emoji", style=discord.ButtonStyle.primary)
        button.callback = self.emoji_callback
        return button


    def footer_button(self):
        button = discord.ui.Button(label="Set Custom Footer", style=discord.ButtonStyle.primary)
        button.callback = self.footer_callback
        return button

    async def image_callback(self, interaction: Interaction):
        if interaction.data['values'][0] == "custom":
            await interaction.response.send_modal(ImageURLModal(self))  # Use modal for image URL
        else:
            giveaway_settings.setdefault(str(interaction.guild_id), {}).pop("image", None)
            save_giveaway_settings(giveaway_settings)
            await interaction.response.send_message("Image set to default.", ephemeral=True)
        await self.update_settings_embed(interaction)

    async def thumbnail_callback(self, interaction: Interaction):
        if interaction.data['values'][0] == "custom":
            await interaction.response.send_modal(ThumbnailURLModal(self))  # Use modal for thumbnail URL
        else:
            giveaway_settings.setdefault(str(interaction.guild_id), {}).pop("thumbnail", None)
            save_giveaway_settings(giveaway_settings)
            await interaction.response.send_message("Thumbnail set to default.", ephemeral=True)
        await self.update_settings_embed(interaction)

    async def color_callback(self, interaction: Interaction):
        if interaction.data['values'][0] == "custom":
            await interaction.response.send_modal(ColorSchemeModal(self))
        else:
            giveaway_settings.setdefault(str(interaction.guild_id), {}).pop("primary_color", None)
            giveaway_settings.setdefault(str(interaction.guild_id), {}).pop("secondary_color", None)
            save_giveaway_settings(giveaway_settings)
            await interaction.response.send_message("Color scheme set to default.", ephemeral=True)
            await self.update_settings_embed(interaction)

    async def emoji_callback(self, interaction: Interaction):
        await interaction.response.send_modal(EmojiModal(self))


    async def footer_callback(self, interaction: Interaction):
        await interaction.response.send_modal(FooterModal(self))

    async def update_settings_embed(self, interaction: Interaction):
        embed = create_settings_embed(interaction.guild)
        await interaction.message.edit(embed=embed)
        #await interaction.followup.send("Settings updated successfully!", ephemeral=True)

class ThumbnailURLModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Thumbnail URL")
        self.view = view
        self.thumbnail_url = TextInput(label="Thumbnail URL", placeholder="Enter the thumbnail URL")
        self.add_item(self.thumbnail_url)

    async def on_submit(self, interaction: Interaction):
        thumbnail_url = self.thumbnail_url.value
        giveaway_settings.setdefault(str(interaction.guild_id), {})["thumbnail"] = thumbnail_url
        save_giveaway_settings(giveaway_settings)
        await self.view.update_settings_embed(interaction)


class ColorSchemeModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Color Scheme")
        self.view = view
        self.primary_color = TextInput(label="Primary Color (Hex)", placeholder="e.g., #FF0000")
        self.secondary_color = TextInput(label="Secondary Color (Hex)", placeholder="e.g., #00FF00")
        self.add_item(self.primary_color)
        self.add_item(self.secondary_color)

    async def on_submit(self, interaction: Interaction):
        primary = self.primary_color.value.strip('#')
        secondary = self.secondary_color.value.strip('#')
        if len(primary) != 6 or len(secondary) != 6:
            await interaction.response.send_message("Invalid color format. Please use 6-digit hex codes.", ephemeral=True)
            return
        giveaway_settings.setdefault(str(interaction.guild_id), {})["primary_color"] = primary
        giveaway_settings[str(interaction.guild_id)]["secondary_color"] = secondary
        save_giveaway_settings(giveaway_settings)
        await self.view.update_settings_embed(interaction)

class EmojiModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Emoji")
        self.view = view
        self.emoji = TextInput(label="Custom Emoji", placeholder="Enter an emoji or custom Discord emoji", max_length=2)
        self.add_item(self.emoji)

    async def on_submit(self, interaction: Interaction):
        emoji = self.emoji.value.strip()
        old_emoji = giveaway_settings.get(str(interaction.guild_id), {}).get("button_emoji", "🎉")

        # Check if it's a custom Discord emoji
        if emoji.startswith('<') and emoji.endsWith('>'):
            # It's a custom emoji, so we'll keep it as is
            new_emoji = emoji
        else:
            # It's a Unicode emoji, so we'll ensure it's a single character
            new_emoji = emoji[:2]  # Take up to two characters to support some composite emojis

        giveaway_settings.setdefault(str(interaction.guild_id), {})["button_emoji"] = new_emoji
        save_giveaway_settings(giveaway_settings)

        await interaction.response.send_message(f"Emoji updated from {old_emoji} to {new_emoji}", ephemeral=True)
        await self.view.update_settings_embed(interaction)

class FooterModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Footer")
        self.view = view
        max_length = 2048 - 1  # Discord embed footer limit minus 1
        self.footer = TextInput(label="Custom Footer Text", style=discord.TextStyle.paragraph, max_length=max_length)
        self.add_item(self.footer)

    async def on_submit(self, interaction: Interaction):
        footer_text = self.footer.value
        giveaway_settings.setdefault(str(interaction.guild_id), {})["footer_text"] = footer_text
        save_giveaway_settings(giveaway_settings)
        await self.view.update_settings_embed(interaction)
        await interaction.response.send_message(f"Submitted footer text to **{interaction.guild.name}**", ephemeral=True)  # Confirmation message


class ImageURLModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Image URL")
        self.view = view
        self.image_url = TextInput(label="Image URL", placeholder="Enter the image URL")
        self.add_item(self.image_url)

    async def on_submit(self, interaction: Interaction):
        image_url = self.image_url.value
        giveaway_settings.setdefault(str(interaction.guild_id), {})["image"] = image_url
        save_giveaway_settings(giveaway_settings)
        await self.view.update_settings_embed(interaction)

class ParticipantsPaginator(discord.ui.View):
    def __init__(self, participants, per_page=10):
        super().__init__(timeout=60)
        self.participants = list(participants)
        self.per_page = per_page
        self.current_page = 1
        self.total_pages = ceil(len(self.participants) / self.per_page)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(1, self.current_page - 1)
        await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages, self.current_page + 1)
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        self.previous_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == self.total_pages

        start_idx = (self.current_page - 1) * self.per_page
        end_idx = start_idx + self.per_page
        current_participants = self.participants[start_idx:end_idx]

        embed = discord.Embed(title="Giveaway Participants", color=0x00ff00)
        embed.description = "\n".join(f"<@{participant}>" for participant in current_participants)
        embed.set_footer(text=f"Page {self.current_page}/{self.total_pages}")

        await interaction.response.edit_message(embed=embed, view=self)

async def resolve_role(guild, role_id):
    return guild.get_role(role_id)

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.green, custom_id="enter_giveaway")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaway = active_giveaways.get(self.giveaway_id)
        if not giveaway or giveaway.ended:
            await interaction.response.send_message("This giveaway has ended.", ephemeral=True)
            return

        if giveaway.role_requirement:
            role = await resolve_role(interaction.guild, giveaway.role_requirement)
            if not role:
                await interaction.response.send_message("The required role for this giveaway no longer exists. Please contact the giveaway host.", ephemeral=True)
                return
            if role not in interaction.user.roles:
                await interaction.response.send_message(f"You need the {role.name} role to enter this giveaway!", ephemeral=True)
                return

        if giveaway.status_requirement:
            print("log 1")
            has_custom_activity = False
            print("log 2")
            guild = interaction.guild
            member = guild.get_member(interaction.user.id)
            for activity in member.activities:
                print(f"Activity: {activity}, Type: {type(activity)}")
                if isinstance(activity, discord.CustomActivity):
                    print(f"Custom Status Detected: {activity.name}")
                    if "gg/klpd" in activity.name:
                        has_custom_activity = True
                        break

            print("log 5")
            if has_custom_activity:
                await interaction.response.send_message("You've successfully entered the giveaway!", ephemeral=True)
            else:
                await interaction.response.send_message("Your custom status must include 'gg/klpd' to enter this giveaway.", ephemeral=True)
                return

        if interaction.user.id in giveaway.participants:
            await interaction.response.send_message("You've already entered this giveaway!", ephemeral=True)
            return

        giveaway.participants.add(interaction.user.id)
        save_giveaways()
        await interaction.response.send_message("You've successfully entered the giveaway!", ephemeral=True)

        # Update the giveaway message with new entry count
        channel = interaction.client.get_channel(giveaway.channel_id)
        message = await channel.fetch_message(giveaway.message_id)
        embed = message.embeds[0]

        for i, field in enumerate(embed.fields):
            if field.name == "Entries":
                embed.set_field_at(i, name="Entries", value=str(len(giveaway.participants)), inline=True)
                break

        await message.edit(embed=embed)


def create_confirmation_embed(giveaway_data, role_requirement):
    embed = discord.Embed(title="Giveaway Confirmation", color=0x00ff00)
    embed.add_field(name="Prize", value=giveaway_data["prize"], inline=False)
    embed.add_field(name="Duration", value=f"{giveaway_data['duration']} seconds", inline=False)
    embed.add_field(name="Winners", value=str(giveaway_data["winners"]), inline=False)

    if giveaway_data.get("notes"):
        embed.add_field(name="Notes", value=giveaway_data["notes"], inline=False)

    return embed

async def update_confirmation_message(interaction: discord.Interaction, role_requirement):
    giveaway_data = interaction.client.temp_giveaway_data
    if role_requirement:
        giveaway_data["role_requirement"] = role_requirement

    embed = create_confirmation_embed(
        giveaway_data,
        giveaway_data.get("role_requirement")
    )

    # Create a confirmation button
    confirm_button = discord.ui.Button(label="Confirm and Launch Giveaway", style=discord.ButtonStyle.green)

    async def confirm_callback(confirm_interaction: discord.Interaction):
        # Defer the interaction to allow more time
        await confirm_interaction.response.defer(ephemeral=True)

        try:
            # Create the giveaway instance
            giveaway = Giveaway(
                channel_id=giveaway_data["channel_id"],
                prize=giveaway_data["prize"],
                duration=giveaway_data["duration"],
                host_id=giveaway_data["host_id"],
                winners=giveaway_data["winners"],
                role_requirement=giveaway_data.get("role_requirement"),
                notes=giveaway_data.get("notes"),
                status_requirement=giveaway_data.get("status_requirement")
            )

            # Save the giveaway in active_giveaways
            giveaway_id = random.randint(1, 100000)  # Generate a unique giveaway ID
            active_giveaways[giveaway_id] = giveaway
            save_giveaways()

            # Create the public giveaway embed
            giveaway_embed = discord.Embed(
                title="🎉 Giveaway!",
                description=f"**Prize:** {giveaway.prize}\n"
                            f"**Winners:** {giveaway.winners}\n"
                            f"**Ends:** <t:{int(giveaway.end_time)}:R>",
                color=0x00ff00
            )

            # Optional fields based on the giveaway settings
            if giveaway.role_requirement:
                role = await resolve_role(confirm_interaction.guild, giveaway.role_requirement)
                giveaway_embed.add_field(name="Role Requirement", value=f"You must have the {role.name} role to participate.", inline=False)
            if giveaway.status_requirement:
                giveaway_embed.add_field(name="Status Requirement", value=f"You must have \"gg/klpd\" somewhere in your status to participate.", inline=False)
            if giveaway.notes:
                giveaway_embed.add_field(name="Notes", value=giveaway.notes, inline=False)
            giveaway_embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/CX8j8C2jGASw8HGroq0vIMrT4KwyzZVMoybKMDritFc/https/cdn.discordapp.com/icons/493063429129502720/a_152d897749da45e310f195129b41aff0.gif")
            # Send the public giveaway message in the specified channel
            channel = confirm_interaction.client.get_channel(giveaway.channel_id)
            giveaway_message = await channel.send(embed=giveaway_embed, view=GiveawayView(giveaway_id))
            giveaway.message_id = giveaway_message.id

            # Notify the host that the giveaway has been successfully started
            await confirm_interaction.followup.send("Giveaway started successfully!", ephemeral=True)

        except Exception as e:
            # Handle any errors and notify the user
            await confirm_interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

    confirm_button.callback = confirm_callback
    view = discord.ui.View()
    view.add_item(confirm_button)

    await interaction.response.edit_message(embed=embed, view=view)

def create_settings_embed(guild):
    settings = giveaway_settings.get(str(guild.id), {})
    embed = Embed(title="Giveaway Settings", color=int(settings.get("primary_color", "00ff00"), 16))
    embed.add_field(name="Image", value="Custom" if "image" in settings else "Default", inline=True)
    embed.add_field(name="Thumbnail", value="Custom" if "thumbnail" in settings else "Default", inline=True)
    embed.add_field(name="Color Scheme", value="Custom" if "primary_color" in settings else "Default", inline=True)
    embed.add_field(name="Button Emoji", value=settings.get("button_emoji", "🎉"), inline=True)
    embed.add_field(name="Custom Footer", value="Set" if "footer_text" in settings else "Default", inline=True)

    if "image" in settings:
        embed.set_image(url=settings["image"])
    if "thumbnail" in settings:
        embed.set_thumbnail(url=settings["thumbnail"])

    footer_text = settings.get("footer_text", f"Server ID: {guild.id}")
    embed.set_footer(text=footer_text)
    return embed

def parse_duration(duration_str):
    total_seconds = 0
    parts = re.findall(r'(\d+)([dhms])', duration_str.lower())
    for value, unit in parts:
        value = int(value)
        if unit == 'd':
            total_seconds += value * 86400
        elif unit == 'h':
            total_seconds += value * 3600
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 's':
            total_seconds += value
    if total_seconds == 0:
        raise ValueError("Invalid duration format")
    return max(total_seconds, 60)  # Ensure minimum duration of 1 minute

async def setup(bot):
    await bot.add_cog(GiveawaysCog(bot))
