import discord
from discord.ext import commands
from discord.ext import menus
from discord import app_commands
from discord.ui import Button, View
import socket
import time
import json
import asyncio

with open('config.json', 'r') as f:
    config = json.load(f)

PREFIX = config['prefix']
DEV_IDS = [int(id) for id in config['devID']]

class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def prepare(self):
        await self.bot.tree.sync()
        print("Bot tree synced.")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.tree.sync()
        print("admin.py loaded.")

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.command(name="remoteping", description="Ping a remote host.")
    async def remoteping(self, interaction:discord.Interaction, host: str, port: int):
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

    @remoteping.error
    async def remoteping_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)

    @commands.has_permissions(administrator=True)
    @commands.command(name="reload")
    async def reload_cog(self, ctx, cog_name: str):
        if ctx.author.id in DEV_IDS:
            try:
                await self.bot.reload_extension(f"cogs.{cog_name}")
                await ctx.send(f"Reloaded {cog_name}.")
            except Exception as e:
                await ctx.send(f"Failed to reload {cog_name}. Error: {e}")
        else:
            await ctx.send("Only a dev can reload cogs.")

    @app_commands.command(name="inrole", description="List members with a specific role.")
    @app_commands.describe(role="The role to list members for")
    async def inrole(self, interaction: discord.Interaction, role: discord.Role):
        if role is None:
            return await interaction.response.send_message('There is no role with that name.', ephemeral=False)

        members_with_roles = [f'{member.name}' for member in interaction.guild.members if role in member.roles]

        if not members_with_roles:
            return await interaction.response.send_message(f'No members found with the role {role.name}.', ephemeral=False)
        members_with_roles.sort()
        composite_members = [members_with_roles[x:x + 20] for x in range(0, len(members_with_roles), 20)]
        embed = discord.Embed(
            title=f"Members with the {role.name} role",
            description="\n".join(composite_members[0]),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page 1/{len(composite_members)}")
        view = RolePaginationView(composite_members, role.name, interaction.user)
        await interaction.response.send_message(embed=embed, view=view)

class RolePaginationView(View):
    def __init__(self, composite_members, role_name, author, timeout=60):
        super().__init__()
        self.current_page = 0
        self.composite_members = composite_members
        self.role_name = role_name
        self.author = author
        self.update_buttons()

    def update_buttons(self):
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == len(self.composite_members) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot interact with this menu.", ephemeral=True)
            return False
        return True

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"Members with the {self.role_name} role",
            description="\n".join(self.composite_members[self.current_page]),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page {self.current_page + 1}/{len(self.composite_members)}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.composite_members) - 1:
            self.current_page += 1
            self.update_buttons()
            await self.update_message(interaction)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="Command cancelled by user.", embed=None, view=self)
        self.stop()

async def setup(bot):
    cog = admin(bot)
    await bot.add_cog(cog)
    await cog.prepare()
