import discord
from discord.ext import commands
from discord import app_commands
import socket
import time
import json

with open('config.json', 'r') as f:
    config = json.load(f)

PREFIX = config['prefix']
DEV_IDS = config['devID']

class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            await self.bot.tree.sync()
        except Exception as e:
            print(e)
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
async def setup(bot):
    await bot.add_cog(admin(bot))
