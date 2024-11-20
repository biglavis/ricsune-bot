import os
import time
import matplotlib.pyplot as plt
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

    # sync commands to the current server
    @commands.command(hidden=True)
    @commands.is_owner()
    # @commands.cooldown(1, 90)
    async def sync(self, ctx: commands.Context):
        async with ctx.channel.typing():
            self.bot.tree.copy_global_to(guild=ctx.guild)
            fmt = await self.bot.tree.sync(guild=ctx.guild)
            await ctx.reply(content=f'Synchronized {len(fmt)} slash commands to the current server.')

    # unsync commands to the current server
    @commands.command(hidden=True)
    @commands.is_owner()
    # @commands.cooldown(1, 90)
    async def unsync(self, ctx: commands.Context):
        async with ctx.channel.typing():
            self.bot.tree.clear_commands(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
            await ctx.reply(content=f'Slash commands have been unsynchronized in this server.')

    # clears all messages in the current channel
    @commands.command(hidden=True)
    @commands.check(is_guild)
    async def clear(self, ctx: commands.Context, limit: int = None):
        await ctx.reply("Are you sure you want to run this command? (yes/no)")

        def check(m: discord.Message): # check if it's the same user and channel
            return m.author == ctx.author and m.channel == ctx.channel

        # wait for response
        try:
            response = await self.bot.wait_for('message', check=check, timeout=10.0)
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
        if not member:
            member = ctx.author
        await ctx.reply(member.avatar)

    @commands.hybrid_command(brief='Display the server avatar of you or another member.', description='Display the server avatar of you or another member.')
    async def savatar(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            member = ctx.author

        await ctx.reply(member.display_avatar)

    @commands.hybrid_command(brief='Get message history.', description='Get message history. Default limit: 1000 messages.')
    async def history(self, ctx: commands.Context, limit: int = 1000):
        if limit < 1:
            return
        if limit > 100000:
            raise Exception("Max limit is 100000.")
    
        msg: discord.Message = None
        if limit > 999:
            msg = await ctx.reply(embed=discord.Embed(title=f"0%", description="This may take a while... <a:loading:1276652002893500500>"))

        timer = time.time()
        iter_count = 0
        msg_count = 0
        async with ctx.channel.typing():
            users = {}
            async for message in ctx.channel.history(limit=limit):
                iter_count += 1
                if msg and (time.time() - timer) > 5:
                    await msg.edit(embed=discord.Embed(title=f"{round(100 * iter_count / limit)}%", description="This may take a while... <a:loading:1276652002893500500>"))
                    timer = time.time()

                if message.author.bot:
                    continue

                msg_count += 1
                if message.author.id not in users:
                    users[message.author.id] = {'name' : message.author.display_name, 'sent' : 0}
                users[message.author.id]['sent'] += 1

            # sort descending
            users = dict(sorted(users.items(), key=lambda item: item[1]['sent'], reverse=True))

            value = ""
            for id in users:
                value += f"<@{id}>: {users[id]['sent']}\n"

            embed=discord.Embed(title="Messages Sent")
            embed.add_field(name=f"Last {limit} messages...", value=value)
            embed.set_image(url="attachment://history.png")

            # group users < 5%
            if (lurkers := [users.pop(id) for id in list(users) if (100 * users[id]['sent'] / msg_count) < 5]):
                users[None] = {'name' : 'Lurkers', 'sent' : sum([lurker['sent'] for lurker in lurkers])}

            # create pie chart
            fig, ax = plt.subplots()

            patches, texts, pcts = ax.pie(
                x=[user['sent'] for user in users.values()], 
                labels=[user['name'] for user in users.values()], 
                autopct='%1.1f%%',
                startangle=90,
                counterclock=False
            )

            for i, patch in enumerate(patches):
                texts[i].set_color(patch.get_facecolor())

            plt.setp(pcts, color='white')
            plt.setp(texts, fontweight=600)

            # save figure
            fig.savefig("./downloads/history.png", bbox_inches='tight', dpi=300)

            if msg:
                await msg.delete()
            await ctx.send(embed=embed, file=discord.File(fp="downloads/history.png"))

            # delete figure
            os.remove("downloads/history.png")

async def setup(bot: commands.Bot):
    await bot.add_cog(ToolCog(bot))
    