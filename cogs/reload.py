from discord.ext import commands
import os
import json

with open('config.json', 'r') as f:
    config = json.load(f)

DEV_IDS = [int(id) for id in config['devID']]

class reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='reloadall')
    async def reloadall(self, ctx):
        if ctx.author.id in DEV_IDS:
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py") and (filename != "reload.py"):
                    try:
                        await self.bot.unload_extension(f"cogs.{filename[:-3]}")
                        await self.bot.load_extension(f"cogs.{filename[:-3]}")
                        await ctx.send(f"Reloaded: {filename}")
                    except Exception as e:
                        await ctx.send(f"Failed to reload {filename}: {e}")
            await self.bot.tree.sync()
            await ctx.send("All cogs reloaded.")
        else:
            await ctx.send("Only a dev can reload cogs.")

async def setup(bot):
    await bot.add_cog(reload(bot))
