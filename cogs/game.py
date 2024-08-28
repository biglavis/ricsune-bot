from modules.game_tools import Minesweeper

import discord
from discord.ext import commands, tasks

class GameCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.games = []

        print(f"cog: {self.qualified_name} loaded")

    @commands.hybrid_command(brief='Minesweeper', description='Minesweeper')
    async def minesweeper(self, ctx: commands.Context):
        self.games.append(Minesweeper(ctx=ctx))
        await self.games[-1].start()
        if not self.watcher.is_running():
            self.watcher.start()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.Member):
        if user.id == self.bot.user.id:
            return
        
        if game := [game for game in self.games if reaction.message.id in [view.message.id for view in game.views]]:
            await game[0].on_reaction(reaction=reaction, user=user)

    @tasks.loop(seconds=5)
    async def watcher(self):
        if not self.games:
            self.watcher.stop()
            return
        
        for game in self.games:
            if game.finished:
                self.games.remove(game)

async def setup(bot: commands.Bot):
    await bot.add_cog(GameCog(bot))
