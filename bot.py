import os
import asyncio
import datetime
from datetime import timedelta
from dotenv import load_dotenv

import discord
from discord.ext import commands

load_dotenv()

TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', owner_id = OWNER_ID, intents=intents)

@bot.event
async def on_ready():
    print(f'\nLogged in as {bot.user} (ID: {bot.user.id})')

    print(f'\n{bot.user} is connected to the following guilds:')
    for guild in bot.guilds:
        print(f'- {guild.name} ({guild.id})')
    print()

@bot.event
async def on_command_error(ctx, exception):
    if isinstance(exception, commands.errors.CommandNotFound):
        await error(ctx, "Command not found.")
    elif isinstance(exception, commands.errors.NotOwner):
        await error(ctx, f'You do not have access to this command.')
    elif isinstance(exception, commands.errors.CheckFailure):
        await error(ctx, f'You do not have access to this command.')
    elif isinstance(exception, commands.errors.CommandOnCooldown):
        await error(ctx, f'Command is on cooldown.\nTry again <t:{round((datetime.datetime.now() + timedelta(seconds=exception.retry_after)).timestamp())}:R>.')
    elif isinstance(exception, commands.errors.CommandError):
        await error(ctx, f'Something went wrong. That\'s all we know.')

async def error(ctx: commands.Context, description: str):
        embed = discord.Embed(title="Woops...", description=description)
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar)
        await ctx.send(embed=embed)

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    await load()
    await bot.start(TOKEN)

asyncio.run(main())
