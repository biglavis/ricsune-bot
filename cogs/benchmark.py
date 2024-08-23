import json
from modules.benchmark_tools import Chimp, Squares, Sequence, show_leaderboard

import discord
from discord.ext import commands

JSON_PATH = 'json//benchmarks.json'

def get_leaderboard() -> dict:
    try:
        with open(JSON_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
class BenchmarkView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.message: discord.Message = None
    
    @discord.ui.button(label="Chimp Test", style=discord.ButtonStyle.green)
    async def chimp_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.delete()
        await Chimp(ctx=self.ctx).start()

    @discord.ui.button(label="Visual Memory", style=discord.ButtonStyle.green)
    async def squares_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.delete()
        await Squares(ctx=self.ctx).start()

    @discord.ui.button(label="Sequence Memory", style=discord.ButtonStyle.green)
    async def sequence_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.delete()
        await Sequence(ctx=self.ctx).start()

    @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.grey)
    async def leaderboard_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.message.delete()
        await show_leaderboard(ctx=self.ctx)

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

    @commands.hybrid_command(brief='Sequence Memory', description='Sequence Memory: Remember an increasingly long pattern of button presses.')
    async def sequence(self, ctx: commands.Context):
        await Sequence(ctx=ctx).start()

    @commands.hybrid_command(brief='See the human benchmark leaderboard.', description='See the human benchmark leaderboard.')
    async def leaderboard(self, ctx: commands.Context):
        await show_leaderboard(ctx=ctx)

    @commands.hybrid_command(brief='Human Benchmark', description='Human Benchmark')
    async def benchmark(self, ctx: commands.Context):
        view = BenchmarkView(ctx=ctx)
        view.message = await ctx.send(view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(BenchmarkCog(bot))
