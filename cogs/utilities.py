import discord
from discord.ext import commands, tasks
import os
import json
from mcstatus.server import JavaServer

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_channel_name.start()
        self.check_status.start()
        self.report.start()
    # Updates the Minecraft player count voie channel
    @tasks.loop(minutes=1)
    async def update_channel_name(self):
        # Minecraft Server Info
        SERVER_IP = '157.90.3.16'
        SERVER_PORT = 40165
        CHANNEL_ID = 1278337388590137345 # VC ID
        log_channel_id = 1278340225512243291
        log_channel = self.bot.get_channel(log_channel_id)
        try:
            server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
            status = server.status()

            channel = self.bot.get_channel(CHANNEL_ID)
            if channel and isinstance(channel, discord.VoiceChannel):
                await channel.edit(name=f"🟢 Players: {status.players.online}/{status.players.max}")
        except Exception as e:
            await log_channel.send(f":x: <@772336857970114590> Failed to retrieve server status or update channel: {e}")

    # Updates the Sexy AF role for online members
    @tasks.loop(seconds=3600)
    async def report(self):
        channel_id = 1278340225512243291
        channel = self.bot.get_channel(channel_id)
        await channel.send(":gear: Utilities cog is functional.")

    @tasks.loop(seconds=120)
    async def check_status(self):
        guild_id = 493063429129502720
        role_id = 771808654805958657
        channel_id = 1278339197878669446

        guild = self.bot.get_guild(guild_id)
        role = discord.utils.get(guild.roles, id=role_id)
        channel = self.bot.get_channel(channel_id)
        count = 0
        if role:
            for member in guild.members:
                if member.status != discord.Status.offline:
                    count = count + 1
                    has_custom_activity = False

                    for activity in member.activities:
                        if isinstance(activity, discord.CustomActivity) and "gg/klpd" in activity.name:
                            has_custom_activity = True
                            break

                    if has_custom_activity:
                        if role not in member.roles:
                            await member.add_roles(role)
                            await channel.send(f":information_source: Assigned {role.name} to {member.name}")
                            await member.send(f"You were given the **Sexy as Fuck** role in KLPD.")
                    else:
                        if role in member.roles:
                            await member.remove_roles(role)
                            await channel.send(f":information_source: Removed {role.name} from {member.name}")
                            await member.send(f"You were removed from the **Sexy as Fuck** role in KLPD.")


async def setup(bot):
    await bot.add_cog(Utilities(bot))
