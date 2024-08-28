import discord
import jishaku
from discord.ext import commands, tasks
from discord import app_commands
import json
from dotenv import load_dotenv
import os
import asyncio

with open('config.json', 'r') as f:
    config = json.load(f)
load_dotenv()

PREFIX = config['prefix']

bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

@tasks.loop(seconds=120)
async def check_status():
    guild_id = 493063429129502720
    role_id = 771808654805958657
    channel_id = 554210303777177609

    guild = bot.get_guild(guild_id)
    role = discord.utils.get(guild.roles, id=role_id)
    channel = bot.get_channel(channel_id)

    await channel.send("Checking status...")
    if role:
        for member in guild.members:
            if member.status != discord.Status.offline:
                print(f"Checking {member.name}")
                has_custom_activity = False

                for activity in member.activities:
                    if isinstance(activity, discord.CustomActivity) and "gg/klpd" in activity.name:
                        has_custom_activity = True
                        break

                if has_custom_activity:
                    if role not in member.roles:
                        await member.add_roles(role)
                        await channel.send(f"Assigned {role.name} to {member.display_name}")
                        await member.send(f"You were given the **Sexy as Fuck** role in KLPD.")
                else:
                    if role in member.roles:
                        await member.remove_roles(role)
                        await channel.send(f"Removed {role.name} from {member.display_name}")
                        await member.send(f"You were removed from the **Sexy as Fuck** role in KLPD.")

@bot.event
async def on_ready():
    check_status.start()
    await load()
    print("---------READY---------")
    print(f"Logged in as: {bot.user.name}")
    print("-----------------------")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and not message.author.bot:
        try:
            await message.channel.send(f"> My prefix is **{PREFIX}**")
        except Exception as e:
            print(f"Error in bot mention: {e}")

    await bot.process_commands(message)

@bot.command(name="inactive_users", description="Lists inactive users")
async def inactive_users(ctx):
    await ctx.send("checking inactive users")
    inactive_threshold = 30  # Days of inactivity to consider
    inactive_users = []

    for member in ctx.guild.members:
        if member.bot:
            continue  # Skip bots
	print(f"message check {member}")
        last_message_time = member.last_message.created_at
        if last_message_time is None:
            # No messages from this member
            inactive_users.append(member)
        else:
            # Calculate duration since last message
            time_since_last_message = (ctx.message.created_at - last_message_time).days
            if time_since_last_message >= inactive_threshold:
                inactive_users.append(member)

    # Send the list of inactive users
    if inactive_users:
        await ctx.send(f"Inactive users: {', '.join(str(user) for user in inactive_users)}")
    else:
        await ctx.send("No inactive users found.")


async def load():
    await bot.load_extension('jishaku')
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            print(f"Loading {filename}...")
            await bot.load_extension(f"cogs.{filename[:-3]}")

async def main():
    async with bot:
        await bot.start(os.getenv('BOT_TOKEN'))


asyncio.run(main())
