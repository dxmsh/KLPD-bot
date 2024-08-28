import discord
from discord.ext import commands

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = 1278341631455789096

    @commands.Cog.listener()
    async def on_ready(self):
        print("Logging Cog loaded")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            embed = discord.Embed(
                title="Message Deleted",
                description=f"Message by {message.author} deleted in {message.channel}",
                color=discord.Color.red()
            )
            embed.add_field(name="Content", value=message.content if message.content else "No text content", inline=False)

            if message.attachments:
                for i, attachment in enumerate(message.attachments, 1):
                    embed.add_field(name=f"Attachment {i}", value=attachment.url, inline=False)

                first_attachment = message.attachments[0].url.lower()
                if first_attachment.endswith(('png', 'jpg', 'jpeg', 'gif')):
                    embed.set_image(url=first_attachment)

            embed.set_footer(text=f"User ID: {message.author.id}")
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        log_channel = self.bot.get_channel(self.log_channel_id)
        if log_channel:
            jump_url = f"https://discord.com/channels/{before.guild.id}/{before.channel.id}/{before.id}"
            embed = discord.Embed(
                title="Message Edited",
                description=f"Message by {before.author} edited in {before.channel}\n[Jump to Message]({jump_url})",
                color=discord.Color.orange()
            )
            embed.add_field(name="Before", value=before.content if before.content else "No text content", inline=False)
            embed.add_field(name="After", value=after.content if after.content else "No text content", inline=False)

            if before.attachments or after.attachments:
                before_attachments = ', '.join(attachment.url for attachment in before.attachments)
                after_attachments = ', '.join(attachment.url for attachment in after.attachments)

                embed.add_field(name="Attachments Before", value=before_attachments or "No attachments", inline=False)

                if before.attachments:  
                    first_before_attachment = before.attachments[0].url.lower()
                    if first_before_attachment.endswith(('png', 'jpg', 'jpeg', 'gif')):
                        embed.set_thumbnail(url=first_before_attachment)

                if after.attachments:
                    first_after_attachment = after.attachments[0].url.lower()
                    if first_after_attachment.endswith(('png', 'jpg', 'jpeg', 'gif')):
                        embed.set_image(url=first_after_attachment)

            embed.set_footer(text=f"User ID: {before.author.id}")
            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Logging(bot))
