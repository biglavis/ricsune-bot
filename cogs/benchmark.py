import json
from modules.benchmark_tools import Chimp, Squares, Sequence

import discord
from discord.ext import commands

JSON_PATH = 'json//benchmarks.json'

def get_leaderboard() -> dict:
    try:
        with open(JSON_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

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
        benchmark_dict = {
            "chimp" : "Chimp Test",
            "squares" : "Visual Memory",
            "sequence" : "Sequence Memory"
        }
        leaderboard = get_leaderboard()
        embed = discord.Embed(title="Human Benchmark Leaderboard")

        for benchmark in ["chimp", "squares", "sequence"]:
            if benchmark not in leaderboard:
                leaderboard[benchmark] = {}

                # save leaderboard
                with open(JSON_PATH, 'w') as f:
                    json.dump(leaderboard, f, indent=4, default=str)
                
            if leaderboard[benchmark]:
                value = ""
                for id in leaderboard[benchmark]:
                    value += f"**{leaderboard[benchmark][id]}**" + " \u200b"*3 + "\u00B7" + " \u200b"*3 + f"<@{id}>\n"
            else:
                value = "[No record]"

            embed.add_field(name=benchmark_dict[benchmark], value=value, inline=False)
            embed.set_footer(text="Test yourself with /benchmark")

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(BenchmarkCog(bot))
