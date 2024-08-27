from modules.game_tools import Minesweeper

import discord
from discord.ext import commands

class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"cog: {self.qualified_name} loaded")

    @commands.hybrid_command(brief='Minesweeper', description='Minesweeper')
    async def minesweeper(self, ctx: commands.Context):
        await Minesweeper(ctx=ctx).start()

async def setup(bot: commands.Bot):
    await bot.add_cog(GameCog(bot))
