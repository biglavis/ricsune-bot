import random
import json
import asyncio

import discord
import discord.colour
from discord.ext import commands

JSON_PATH = 'json//benchmarks.json'

class Button(discord.ui.Button):
    def __init__(self, label: str = "\u200b", style: discord.ButtonStyle = discord.ButtonStyle.grey, custom_id: str = None, row: int = None):
        super().__init__(label=label, style=style, custom_id=custom_id, row=row)
        self.value = None

    async def callback(self, interaction: discord.Interaction):
        await self.view.interacted(button=self, interaction=interaction)

class ChimpView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.message: discord.Message = None

        self.level = 0
        self.stage = 1
        self.strikes = 0
        self.pause = True

        self.add_item(Button(label="Start Test", style=discord.ButtonStyle.green))

    async def on_timeout(self):
        self.remove_all()
        await self.complete()

    def scramble(self):
        '''
        Adds buttons and scrambles numbers.
        '''
        self.stage = 1

        for i in range(25):
            self.add_item(Button(custom_id=f"button_{i}"))

        values = list(range(1, self.level+1)) + [None] * (25 - self.level)
        random.shuffle(values)
        
        button: Button
        for i, button in enumerate(self.children):
            button.value = values[i]

        self.reveal()

    def reveal(self):
        '''
        Reveals the numbers.
        '''
        button: Button
        for button in self.children:
            if button.value:
                button.style = discord.ButtonStyle.blurple
                button.label = str(button.value)
                button.disabled = False
            else:
                button.style = discord.ButtonStyle.grey
                button.label = "\u200b"
                button.disabled = True

        self.hidden = False

    def hide(self):
        '''
        Hides the numbers.
        '''
        button: Button
        for button in self.children:
            if button.value:
                button.label = "\u200b"

        self.hidden = True

    def remove_all(self):
        '''
        Removes all children from this view.
        '''
        while self.children:
            self.remove_item(self.children[0])

    async def interacted(self, button: discord.ui.Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.defer()
            return
        
        if self.pause:
            self.pause = False

            if self.level == 0:
                self.level = 4

            self.remove_all()
            self.scramble()

            await interaction.response.edit_message(embed=None, view=self)
            return

        if button.value != self.stage:
            await self.failed(interaction=interaction)
            return
        
        if self.stage == self.level:
            await self.passed(interaction=interaction)
            return
         
        self.stage += 1
        
        if self.level > 4 and not self.hidden:
            self.hide()

        button.style = discord.ButtonStyle.grey
        button.label = "\u200b"
        button.disabled = True

        await interaction.response.edit_message(view=self)

    async def failed(self, interaction: discord.Interaction):
        '''
        User failed the level.
        '''
        self.pause = True
        self.strikes += 1
        self.remove_all()

        if self.strikes == 3:
            await interaction.response.defer()
            await self.complete()
            return

        embed = discord.Embed(title=f"Numbers: {self.level}", description=f"Strikes: **{self.strikes} of 3**", color=discord.Colour.red())
        self.add_item(Button(label="Continue", style=discord.ButtonStyle.green))

        await interaction.response.edit_message(embed=embed, view=self)

    async def passed(self, interaction: discord.Interaction):
        '''
        User passed the level.
        '''
        self.pause = True
        self.level += 1
        self.remove_all()

        if self.level > 25:
            await interaction.response.defer()
            await self.complete()
            return

        embed = discord.Embed(title=f"Numbers: {self.level}", description=f"Strikes: **{self.strikes} of 3**")
        self.add_item(Button(label="Continue", style=discord.ButtonStyle.green))

        await interaction.response.edit_message(embed=embed, view=self)

    async def complete(self):
        '''
        User completed the test / striked out.
        '''
        if self.level == 4:
            score = 0
        else:
            score = self.level - 1
            
        leaderboard = get_leaderboard()

        if 'chimp' not in leaderboard:
            leaderboard['chimp'] = {}

        # if user not in leaderboard or user has new highscore
        if str(self.ctx.author.id) not in leaderboard['chimp'] or score > leaderboard['chimp'][str(self.ctx.author.id)]:
            leaderboard['chimp'][str(self.ctx.author.id)] = score

        # sort leaderboard
        leaderboard['chimp'] = dict(sorted(leaderboard['chimp'].items(), key=lambda item: item[1], reverse=True))
        if len(leaderboard['chimp']) > 5:
            leaderboard['chimp'] = leaderboard['chimp'][:5]

        # save leaderboard
        with open(JSON_PATH, 'w') as f:
            json.dump(leaderboard, f, indent=4, default=str)

        description="**Leaderboard**"
        for id in leaderboard['chimp']:
            description += f"\n**{leaderboard['chimp'][id]}**" + " \u200b"*3 + "\u00B7" + " \u200b"*3 + f"<@{id}>"

        embed = discord.Embed(title=f"Your Score: {score}", description=description)

        await self.message.edit(embed=embed, view=self)
        self.stop()

class TilesView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.message: discord.Message = None

    async def generate(self, rows: int, columns: int, values: list[int]):
        for i in range(rows):
            for j in range(columns):
                self.add_item(Button(row=i))

        button: Button
        for i, button in enumerate(self.children):
            button.value = values[i]

        await self.message.edit(view=self)

    async def reveal(self):
        button: Button
        for button in self.children:
            if button.value:
                button.style = discord.ButtonStyle.blurple

        await self.message.edit(view=self)

class Tiles():
    def __init__(self, ctx: commands.Context, views = list[TilesView]):
        self.ctx = ctx
        self.views = views
        self.level = 11
        self.strikes = 0
        self.lives = 3

    async def scramble(self):
        if self.level < 3:
            grid = [3, 3]
        elif self.level < 7:
            grid = [4, 4]
        elif self.level < 11:
            grid = [5, 5]
        elif self.level < 16:
            grid = [5, 7]
        else:
            grid = [5, 10]

        values = [True]*(self.level + 2) + [False]*(grid[0]*grid[1] - (self.level + 2))
        random.shuffle(values)

        await self.views[0].generate(rows=min(5, grid[1]), columns=grid[0], values=values[:min(25, grid[0]*grid[1])])
        await self.views[1].generate(rows=max(0, grid[1]-5), columns=grid[0], values=values[min(25, grid[0]*grid[1]):])

        await self.views[0].reveal()
        await self.views[1].reveal()

class BenchmarkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(brief='Are You Smarter Than a Chimpanzee?', description='Are You Smarter Than a Chimpanzee?')
    async def chimp(self, ctx: commands.Context):
        description = "Click the squares in order according to their numbers.\nThe test will get progressively harder."
        embed = discord.Embed(title="Are You Smarter Than a Chimpanzee?", description=description)

        view = ChimpView(ctx=ctx)
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command()
    async def tiles(self, ctx: commands.Context):
        views = [TilesView(ctx=ctx), TilesView(ctx=ctx)]
        views[0].message = await ctx.send(content="\u200b", view=views[0])
        views[1].message = await ctx.send(content="\u200b", view=views[1])

        x = Tiles(ctx=ctx, views=views)
        await x.scramble()

def get_leaderboard() -> dict:
    try:
        with open(JSON_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

async def setup(bot: commands.Bot):
    await bot.add_cog(BenchmarkCog(bot))
