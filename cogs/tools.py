import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

load_dotenv()

MY_GUILD = int(os.getenv("MY_GUILD"))

class ToolCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"cog: {self.qualified_name} loaded")

    # checks if command was sent from MY_GUILD
    def is_guild(ctx: commands.Context):
        return ctx.guild.id == MY_GUILD
    
    @commands.hybrid_command(brief='Ping the bot.', description='Ping the bot.')
    async def ping(self, ctx: commands.Context):
        await ctx.reply(content=f'***Pong!*** ({round(self.bot.latency * 1000)}ms)')

    # sync commands to current server
    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.cooldown(1, 90)
    async def sync(self, ctx: commands.Context):
        async with ctx.channel.typing():
            self.bot.tree.copy_global_to(guild=ctx.guild)
            fmt = await self.bot.tree.sync(guild=ctx.guild)
            await ctx.reply(content=f'Synced {len(fmt)} commands to the current server.')

    # clears all messages in the current channel
    @commands.command(hidden=True)
    @commands.check(is_guild)
    async def clear(self, ctx: commands.Context, limit: int = None):
        await ctx.reply("Are you sure you want to run this command? (yes/no)")

        def check(m: discord.Message): # check if it's the same user and channel
            return m.author == ctx.author and m.channel == ctx.channel

        # wait for response
        try:
            response = await self.bot.wait_for('message', check=check, timeout=30.0)
        except:
            return

        # if response is different than yes / y - return
        if response.content.lower() not in ("yes", "y"):
            return
        
        if limit != None:
            limit += 3

        async with ctx.channel.typing():
            await ctx.channel.purge(limit=limit)

    @commands.hybrid_command(brief='Display the avatar of you or another member.', description='Display the avatar of you or another member.')
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        if member is None:
            member = ctx.author
        await ctx.reply(member.avatar)

    @commands.hybrid_command(brief='Display the server avatar of you or another member.', description='Display the server avatar of you or another member.')
    async def savatar(self, ctx: commands.Context, member: discord.Member = None):
        if member is None:
            member = ctx.author
        if not (avatar := member.guild_avatar):
            avatar = member.avatar

        await ctx.reply(avatar)

async def setup(bot: commands.Bot):
    await bot.add_cog(ToolCog(bot))
    