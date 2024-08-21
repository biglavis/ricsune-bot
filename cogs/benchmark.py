from modules.benchmark_tools import Chimp, Squares

import discord
from discord.ext import commands

class BenchmarkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"cog: {self.qualified_name} loaded")

    @commands.hybrid_command(brief='Chimp Test', description='Chimp Test: Are you smarter than a chimpanzee?')
    async def chimp(self, ctx: commands.Context):
        await Chimp(ctx=ctx).start()

    @commands.hybrid_command(brief='Visual Memory', description='Visual Memory: Remember an increasingly large board of squares.')
    async def squares(self, ctx: commands.Context):
        await Squares(ctx=ctx).start()

async def setup(bot: commands.Bot):
    await bot.add_cog(BenchmarkCog(bot))
