import random
import json
import datetime
import asyncio

import discord
import discord.colour
from discord.ext import commands

JSON_PATH = 'json//benchmarks.json'

def get_leaderboard() -> dict:
    try:
        with open(JSON_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    
async def show_leaderboard(ctx: commands.Context):
        benchmark_dict = {
            "chimp" : "Chimp Test",
            "squares" : "Visual Memory",
            "sequence" : "Sequence Memory"
        }
        lb = get_leaderboard()
        embed = discord.Embed(title="Human Benchmark Leaderboard")

        for benchmark in ["chimp", "squares", "sequence"]:
            if benchmark not in lb:
                lb[benchmark] = {}

                # save leaderboard
                with open(JSON_PATH, 'w') as f:
                    json.dump(lb, f, indent=4, default=str)
                
            if lb[benchmark]:
                value = ""
                for id in lb[benchmark]:
                    value += f"**{lb[benchmark][id]}**" + " \u200b"*3 + "\u00B7" + " \u200b"*3 + f"<@{id}>\n"
            else:
                value = "[No record]"

            embed.add_field(name=benchmark_dict[benchmark], value=value, inline=False)
            embed.set_footer(text="Test yourself with /benchmark")

        await ctx.send(embed=embed)

class Button(discord.ui.Button):
    def __init__(self, label: str = "\u200b", style: discord.ButtonStyle = discord.ButtonStyle.grey, custom_id: str = None, disabled: bool = False, row: int = None):
        super().__init__(label=label, style=style, custom_id=custom_id, disabled=disabled, row=row)
        self.value = None

    async def callback(self, interaction: discord.Interaction):
        await self.view.interacted(button=self, interaction=interaction)

# Chimp Test
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

class ChimpView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.controller: Chimp = None
        self.message: discord.Message = None

    async def on_timeout(self):
        await self.controller.completed()

    def generate(self, rows: int, columns: int, values: list[int]):
        '''
        Adds buttons and assigns numbers.
        '''
        self.remove_all()

        for i in range(rows):
            for j in range(columns):
                self.add_item(Button(disabled=True, row=i))

        button: Button
        for i, button in enumerate(self.children):
            button.value = values[i]

    def reveal(self):
        '''
        Reveals the numbers.
        '''
        button: Button
        for button in self.children:
            if button.value != None:
                button.style = discord.ButtonStyle.blurple
                button.label = str(button.value + 1) 
                button.disabled = False
            else:
                button.style = discord.ButtonStyle.grey
                button.label = "\u200b"
                button.disabled = True

    def hide(self):
        '''
        Hides the numbers.
        '''
        button: Button
        for button in self.children:
            button.label = "\u200b"

    def remove_all(self):
        '''
        Removes all children from this view.
        '''
        while self.children:
            self.remove_item(self.children[0])

    async def update(self, **kwargs):
        '''
        Edit self.message
        '''
        if 'view' not in kwargs:
            kwargs['view'] = self
        self.message = await self.message.edit(**kwargs)

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.defer()
            return
        
        await self.controller.interacted(button=button, interaction=interaction)

class Chimp():
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.view: ChimpView

        self.level = 0
        self.stage = 0
        self.lives = 3

    async def start(self):
        '''
        Start the Chimp test.
        '''
        description = "Click the squares in order according to their numbers.\nThe test will get progressively harder."
        embed = discord.Embed(title="Are You Smarter Than a Chimpanzee?", description=description)

        self.view = ChimpView(ctx=self.ctx)
        self.view.controller = self
        self.view.add_item(Button(label="Start", style=discord.ButtonStyle.green))
        
        self.view.message = await self.ctx.send(embed=embed, view=self.view)

    async def scramble(self):
        '''
        Adds buttons and scrambles numbers.
        '''
        values = list(range(self.level)) + [None] * (25 - self.level)
        random.shuffle(values)
        
        self.view.generate(rows=5, columns=5, values=values)
        self.view.reveal()

        await self.view.update(content=f"`Level: {self.level}   Lives: {'♥'*self.lives}`", embed=None)

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if self.level == 0:
            await interaction.response.defer()
            self.level = 4
            await self.scramble()
            return

        if button.value != self.stage:
            await self.failed(button=button, interaction=interaction)
            return
        
        self.stage += 1
        
        if self.stage == self.level:
            await self.passed(button=button, interaction=interaction)
            return
        
        if self.level > 4 and self.stage == 1:
            self.view.hide()
            await self.view.update()

        button.style = discord.ButtonStyle.grey
        button.label = "\u200b"
        button.disabled = True

        await interaction.response.edit_message(view=button.view)

    async def passed(self, button: Button, interaction: discord.Interaction):
        '''
        User passed the level.
        '''
        self.level += 1
        self.stage = 0

        button.style = discord.ButtonStyle.green
        button.disabled = True

        await interaction.response.edit_message(view=button.view)
        await asyncio.sleep(1)

        if self.level > 25:
            await self.completed()
        else:
            await self.scramble()

    async def failed(self, button: Button, interaction: discord.Interaction):
        '''
        User failed the level.
        '''
        self.lives -= 1
        self.stage = 0

        button.style = discord.ButtonStyle.red

        b: Button
        for b in self.view.children:
            b.disabled = True

        await interaction.response.edit_message(view=button.view)
        await asyncio.sleep(1)

        if self.lives == 0:
            await self.completed()
        else:
            await self.scramble()

    async def completed(self):
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
        if str(self.ctx.author.id) not in leaderboard['chimp'] or (score > 0 and score > leaderboard['chimp'][str(self.ctx.author.id)]):
            leaderboard['chimp'][str(self.ctx.author.id)] = score

        # sort leaderboard
        leaderboard['chimp'] = dict(sorted(leaderboard['chimp'].items(), key=lambda item: item[1], reverse=True))

        # save leaderboard
        with open(JSON_PATH, 'w') as f:
            json.dump(leaderboard, f, indent=4, default=str)

        description="**Leaderboard**"
        for id in leaderboard['chimp']:
            description += f"\n**{leaderboard['chimp'][id]}**" + " \u200b"*3 + "\u00B7" + " \u200b"*3 + f"<@{id}>"

        embed = discord.Embed(title=f"Your Score: {score}", description=description)

        await self.view.update(content=None, embed=embed, view=None)
        self.view.stop()

# Visual Memory
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

class SquaresView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.controller: Squares = None
        self.message: discord.Message = None

    async def on_timeout(self):
        await self.controller.completed()

    def generate(self, rows: int, columns: int, values: list[int]):
        '''
        Adds buttons and assigns squares.
        '''
        self.remove_all()

        for i in range(rows):
            for j in range(columns):
                self.add_item(Button(disabled=True, row=i))

        button: Button
        for i, button in enumerate(self.children):
            button.value = values[i]

    def reveal(self):
        '''
        Reveals the squares.
        '''
        if not self.children:
            return
        
        button: Button
        for button in self.children:
            if button.value:
                button.style = discord.ButtonStyle.blurple
            button.disabled = True

    def hide(self):
        '''
        Hides the squares.
        '''
        if not self.children:
            return
        
        button: Button
        for button in self.children:
            button.style = discord.ButtonStyle.grey
            button.disabled = False

    def remove_all(self):
        '''
        Removes all children from this view.
        '''
        while self.children:
            self.remove_item(self.children[0])

    async def update(self, **kwargs):
        '''
        Edit self.message
        '''
        if 'view' not in kwargs:
            kwargs['view'] = self
        self.message = await self.message.edit(**kwargs)

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.defer()
            return
        
        await self.controller.interacted(button=button, interaction=interaction)

class Squares():
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.views: list[SquaresView] = None

        self.level = 0
        self.stage = 0
        self.lives = 3
        self.strikes = 0

    async def start(self):
        '''
        Start the visual memory test.
        '''
        self.views = [SquaresView(ctx=self.ctx), SquaresView(ctx=self.ctx)]

        self.views[0].controller = self
        self.views[1].controller = self

        embed = discord.Embed(title="Visual Memory Test", description="Memorize the squares.")
        self.views[0].add_item(Button(label="Start", style=discord.ButtonStyle.green))

        self.views[0].message = await self.ctx.send(embed=embed, view=self.views[0])
        self.views[1].message = await self.ctx.channel.send(content="\u200b")

    async def scramble(self):
        '''
        Add buttons and scramble squares.
        '''
        if self.level < 3:
            grid = [3, 3]
        elif self.level < 6:
            grid = [4, 4]
        elif self.level < 10:
            grid = [5, 5]
        elif self.level < 15:
            grid = [5, 7]
        else:
            grid = [5, 10]

        values = [True]*(self.level + 2) + [False]*(grid[0]*grid[1] - (self.level + 2))
        random.shuffle(values)

        self.views[0].generate(rows=min(5, grid[1]), columns=grid[0], values=values[:grid[0]*min(5, grid[1])])
        self.views[1].generate(rows=max(0, grid[1]-5), columns=grid[0], values=values[grid[0]*min(5, grid[1]):])

        await self.views[0].update(content=f"`Level: {self.level}   Lives: {'♥'*self.lives}`", embed=None)
        await self.views[1].update()

        await asyncio.sleep(1)

        for view in self.views:
            view.reveal()
            await view.update()

        await asyncio.sleep(2)

        for view in self.views:
            view.hide()
            await view.update()

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if self.level == 0:
            await interaction.response.defer()
            self.level += 1
            await self.scramble()
            return
        
        if not button.value:
            self.strikes += 1

            button.style = discord.ButtonStyle.red
            button.disabled = True

            if self.strikes < 3:
                await interaction.response.edit_message(view=button.view)
                return

            await self.failed(button=button, interaction=interaction)
            return

        self.stage += 1

        if self.stage == self.level + 2:
            await self.passed(button=button, interaction=interaction)
            return

        button.style = discord.ButtonStyle.blurple
        button.disabled = True

        await interaction.response.edit_message(view=button.view)

    async def passed(self, button: Button, interaction: discord.Interaction):
        '''
        User passed the level.
        '''
        self.level += 1
        self.stage = 0
        self.strikes = 0

        for view in self.views:
            b: Button
            for b in view.children:
                if b.value:
                    b.style = discord.ButtonStyle.green
                b.disabled = True

        view = self.views[0] if self.views[0] != button.view else self.views[1]
        await interaction.response.edit_message(view=button.view)
        await view.update()
        
        await asyncio.sleep(1)

        if self.level > 23:
            await self.completed()
        else:
            await self.scramble()

    async def failed(self, button: Button, interaction: discord.Interaction):
        '''
        User failed the level.
        '''
        self.stage = 0
        self.lives -= 1
        self.strikes = 0

        for view in self.views:
            b: Button
            for b in view.children:
                if b.disabled:
                    b.style = discord.ButtonStyle.red
                b.disabled = True

        view = self.views[0] if self.views[0] != button.view else self.views[1]
        await interaction.response.edit_message(view=button.view)
        await view.update()

        await asyncio.sleep(1)

        if self.lives == 0:
            await self.completed()
        else:
            await self.scramble()

    async def completed(self):
        '''
        User completed the test / striked out.
        '''
        score = self.level - 1
        leaderboard = get_leaderboard()

        if 'squares' not in leaderboard:
            leaderboard['squares'] = {}

        # if user not in leaderboard or user has new highscore
        if str(self.ctx.author.id) not in leaderboard['squares'] or (score > 0 and score > leaderboard['squares'][str(self.ctx.author.id)]):
            leaderboard['squares'][str(self.ctx.author.id)] = score

        # sort leaderboard
        leaderboard['squares'] = dict(sorted(leaderboard['squares'].items(), key=lambda item: item[1], reverse=True))

        # save leaderboard
        with open(JSON_PATH, 'w') as f:
            json.dump(leaderboard, f, indent=4, default=str)

        description="**Leaderboard**"
        for id in leaderboard['squares']:
            description += f"\n**{leaderboard['squares'][id]}**" + " \u200b"*3 + "\u00B7" + " \u200b"*3 + f"<@{id}>"

        embed = discord.Embed(title=f"Your Score: {score}", description=description)

        await self.views[1].message.delete()
        await self.views[0].update(content=None, embed=embed, view=None)
        
        for view in self.views:
            view.stop()

# Sequence Memory
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

class SequenceView(discord.ui.View):
    def __init__(self, ctx: commands.Context, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.controller: Chimp = None
        self.message: discord.Message = None

    async def on_timeout(self):
        await self.controller.completed()

    def generate(self, rows: int, columns: int, values: list[int]):
        '''
        Adds buttons and assigns numbers.
        '''
        self.remove_all()

        for i in range(rows):
            for j in range(columns):
                self.add_item(Button(disabled=True, row=i))

        button: Button
        for i, button in enumerate(self.children):
            button.value = values[i]

    def remove_all(self):
        '''
        Removes all children from this view.
        '''
        while self.children:
            self.remove_item(self.children[0])

    async def update(self, **kwargs):
        '''
        Edit self.message
        '''
        if 'view' not in kwargs:
            kwargs['view'] = self
        self.message = await self.message.edit(**kwargs)

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.defer()
            return
        
        await self.controller.interacted(button=button, interaction=interaction)

class Sequence():
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.view: SequenceView = None

        self.sequence = []
        self.level = 0
        self.stage = 0

    async def start(self):
        '''
        Start the sequence memory test.
        '''
        embed = discord.Embed(title="Sequence Memory Test", description="Memorize the pattern.")

        self.view = SequenceView(ctx=self.ctx)
        self.view.controller = self
        self.view.add_item(Button(label="Start", style=discord.ButtonStyle.green))
        
        self.view.message = await self.ctx.send(embed=embed, view=self.view)

    def append_sequence(self):
        '''
        Adds a random number to the sequence.
        '''
        n = random.randint(0, 8)
        if len(self.sequence) > 0:
            while (n == self.sequence[-1]): n = random.randint(0, 8)

        self.sequence.append(n)

    async def show_sequence(self):
        button: Button
        for button in self.view.children:
            button.disabled = True
            button.style = discord.ButtonStyle.grey
        
        await self.view.update(content=f"`Level: {self.level}`", embed=None)
        await asyncio.sleep(1)

        for i in self.sequence:
            self.view.children[i].style = discord.ButtonStyle.blurple
            await self.view.update()
            await asyncio.sleep(0.5)
            self.view.children[i].style = discord.ButtonStyle.grey
        
        for button in self.view.children:
            button.disabled = False

        await self.view.update()

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if self.level == 0:
            await interaction.response.defer()
            self.level += 1
            self.view.generate(rows=3, columns=3, values=list(range(9)))
            self.append_sequence()
            await self.show_sequence()
            return

        if button.value != self.sequence[self.stage]:
            await self.failed(button=button, interaction=interaction)
            return

        self.stage += 1

        if self.stage == self.level:
            await self.passed(button=button, interaction=interaction)
            return

        await interaction.response.defer()

    async def passed(self, button: Button, interaction: discord.Interaction):
        '''
        User passed the level.
        '''
        self.level += 1
        self.stage = 0

        button: Button
        for button in self.view.children:
            button.style = discord.ButtonStyle.green
            button.disabled = True

        await interaction.response.edit_message(view=button.view)
        await asyncio.sleep(1)
        
        self.append_sequence()
        await self.show_sequence()

    async def failed(self, button: Button, interaction: discord.Interaction):
        '''
        User failed the level.
        '''
        button: Button
        for button in self.view.children:
            button.style = discord.ButtonStyle.red
            button.disabled = True

        await interaction.response.edit_message(view=button.view)
        await asyncio.sleep(1)

        await self.completed()

    async def completed(self):
        '''
        User completed the test.
        '''
        score = self.level - 1
        leaderboard = get_leaderboard()

        if 'sequence' not in leaderboard:
            leaderboard['sequence'] = {}

        # if user not in leaderboard or user has new highscore
        if str(self.ctx.author.id) not in leaderboard['sequence'] or (score > 0 and score > leaderboard['sequence'][str(self.ctx.author.id)]):
            leaderboard['sequence'][str(self.ctx.author.id)] = score

        # sort leaderboard
        leaderboard['sequence'] = dict(sorted(leaderboard['sequence'].items(), key=lambda item: item[1], reverse=True))

        # save leaderboard
        with open(JSON_PATH, 'w') as f:
            json.dump(leaderboard, f, indent=4, default=str)

        description="**Leaderboard**"
        for id in leaderboard['sequence']:
            description += f"\n**{leaderboard['sequence'][id]}**" + " \u200b"*3 + "\u00B7" + " \u200b"*3 + f"<@{id}>"

        embed = discord.Embed(title=f"Your Score: {score}", description=description)

        await self.view.update(content=None, embed=embed, view=None)
        self.view.stop()
