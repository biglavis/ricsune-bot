import random
import json
import asyncio

import discord
import discord.colour
from discord.ext import commands

class Button(discord.ui.Button):
    def __init__(self, label: str = "\u200b", style: discord.ButtonStyle = discord.ButtonStyle.grey, custom_id: str = None, disabled: bool = False, row: int = None):
        super().__init__(label=label, style=style, custom_id=custom_id, disabled=disabled, row=row)
        self.value = None

    async def callback(self, interaction: discord.Interaction):
        await self.view.interacted(button=self, interaction=interaction)

# Minesweeper
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
NUM_MINES = 8

class MinesweeperView(discord.ui.View):
    def __init__(self, index: int, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.controller: Minesweeper = None
        self.message: discord.Message = None
        self.index = index

        self.generate(rows=5, columns=5)

    async def on_timeout(self):
        await self.controller.game_over()

    def generate(self, rows: int, columns: int):
        '''
        Create buttons.
        '''
        for i in range(rows):
            for j in range(columns):
                self.add_item(Button(style=discord.ButtonStyle.blurple, row=i))
                self.children[-1].value = (i + 5*self.index, j)

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
        await self.controller.interacted(button=button, interaction=interaction)

class Minesweeper():
    def __init__(self, ctx: commands.Context):
        self.ctx = ctx
        self.views: list[MinesweeperView] = None

        self.grid = None
        self.flagging = False
        self.flags = 8
        self.digs = 0

        self.finished = False

    async def start(self):
        self.views = [MinesweeperView(index=0), MinesweeperView(index=1)]

        self.views[0].controller = self
        self.views[1].controller = self

        self.views[0].message = await self.ctx.send(content=f"`🙂   🚩 {self.flags}   [Clicking]`", view=self.views[0])
        self.views[1].message = await self.ctx.send(view=self.views[1])

        await self.views[1].message.add_reaction("👆")
        await self.views[1].message.add_reaction("🚩")

    def generate(self, first_pos = tuple[int, int]):
        '''
        Generates grid.
        '''
        while True:
            self.grid = [[0,0,0,0,0] for _ in range(10)]
            self.set_mines(first_pos=first_pos)
            self.set_values()

            if self.grid[first_pos[0]][first_pos[1]] == 0:
                return

    def set_mines(self, first_pos = tuple[int, int]):
        '''
        Places mines.
        '''
        count = 0
        while count < NUM_MINES:
            val = random.randint(0, 49)

            r = val // 5
            col = val % 5

            if (r, col) != first_pos and self.grid[r][col] != -1:
                self.grid[r][col] = -1
                count += 1

    def set_values(self):
        '''
        Determines the values for each sqaure.
        '''
        for r in range(10):
            for col in range(5):
                # skip if mine
                if self.grid[r][col] == -1:
                    continue

                # check up
                if r > 0 and self.grid[r-1][col] == -1:
                    self.grid[r][col] += 1
                # check down
                if r < 9 and self.grid[r+1][col] == -1:
                    self.grid[r][col] += 1
                # check left
                if col > 0 and self.grid[r][col-1] == -1:
                    self.grid[r][col] += 1
                # check right
                if col < 4 and self.grid[r][col+1] == -1:
                    self.grid[r][col] += 1
                # check top left
                if r > 0 and col > 0 and self.grid[r-1][col-1] == -1:
                    self.grid[r][col] += 1
                # check top right
                if r > 0 and col < 4 and self.grid[r-1][col+1] == -1:
                    self.grid[r][col] += 1
                # check bottom left
                if r < 9 and col > 0 and self.grid[r+1][col-1] == -1:
                    self.grid[r][col] += 1
                # check botom right
                if r < 9 and col < 4 and self.grid[r+1][col+1] == -1:
                    self.grid[r][col] += 1

    async def on_reaction(self, reaction: discord.Reaction, user: discord.Member):
        '''
        Reaction callback.
        '''
        if self.finished:
            return
        
        if reaction.message.id != self.views[1].message.id:
            await reaction.remove(user)
            return
        
        if user.id != self.ctx.author.id:
            await reaction.remove(user)
            return
        
        if reaction.emoji == "🚩" and not self.flagging:
            self.flagging = True

            for view in self.views:
                button: Button
                for button in view.children:
                    if button.label == "🚩":
                        button.disabled = False

            await self.views[0].update(content=f"`🙂   🚩 {self.flags}   [Flagging]`")
            await self.views[1].update()

        elif reaction.emoji == "👆" and self.flagging:
            self.flagging = False

            for view in self.views:
                button: Button
                for button in view.children:
                    if button.label == "🚩":
                        button.disabled = True

            await self.views[0].update(content=f"`🙂   🚩 {self.flags}   [Clicking]`")
            await self.views[1].update()

        await reaction.remove(user)

    async def interacted(self, button: Button, interaction: discord.Interaction):
        '''
        Button interaction callback.
        '''
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.defer()
            return
        
        if not self.grid and not self.flagging:
            # remove flags on first dig
            self.flags = 8
            for view in self.views:
                b: Button
                for b in view.children:
                    b.label = "\u200b"
                    b.disabled = False

            self.generate(first_pos=button.value)

        r, col = button.value

        if self.flagging:
            await self.flag(button=button, interaction=interaction)
            return

        if self.grid[r][col] == -1:
            await interaction.response.defer()
            await self.lose()
            return

        self.dig(r, col)

        if self.digs == 50 - NUM_MINES:
            await interaction.response.defer()
            await self.win()
            return

        view = self.views[0] if self.views[0] != button.view else self.views[1]
        await interaction.response.edit_message(view=button.view)
        await view.update()

    def dig(self, r: int, col: int):
        button: Button = self.views[r // 5].children[(r % 5) * 5 + col]

        if button.disabled:
            return
            
        button.style = discord.ButtonStyle.grey
        button.disabled = True
        self.digs += 1

        if self.grid[r][col] == 0:
            # check up
            if r > 0 and self.grid[r-1][col] != -1:
                self.dig(r-1, col)
            # check down
            if r < 9 and self.grid[r+1][col] != -1:
                self.dig(r+1, col)
            # check left
            if col > 0 and self.grid[r][col-1] != -1:
                self.dig(r, col-1)
            # check right
            if col < 4 and self.grid[r][col+1] != -1:
                self.dig(r, col+1)
            # check top left
            if r > 0 and col > 0 and self.grid[r-1][col-1] != -1:
                self.dig(r-1, col-1)
            # check top right
            if r > 0 and col < 4 and self.grid[r-1][col+1] != -1:
                self.dig(r-1, col+1)
            # check bottom left
            if r < 9 and col > 0 and self.grid[r+1][col-1] != -1:
                self.dig(r+1, col-1)
            # check botom right
            if r < 9 and col < 4 and self.grid[r+1][col+1] != -1:
                self.dig(r+1, col+1)
                
        else:
            button.label = str(self.grid[r][col])

    async def flag(self, button: Button, interaction: discord.Interaction):
        if button.label != "🚩":
            button.label = "🚩"
            self.flags -= 1

        else:
            button.label = "\u200b"
            self.flags += 1

        await self.views[0].update(content=f"`🙂   🚩 {self.flags}   [Flagging]`")
        await interaction.response.edit_message(view=button.view)

    async def win(self):
        for view in self.views:
            button: Button
            for button in view.children:
                if button.disabled and button.label != "🚩":
                    button.style = discord.ButtonStyle.green
                else:
                    button.style = discord.ButtonStyle.grey
                button.disabled = True

        await self.views[0].update(content=f"`🥳   🚩 {self.flags}   [Clicking]`")
        await self.views[1].update()

        await self.game_over()

    async def lose(self):
        for view in self.views:
            button: Button
            for button in view.children:
                if self.grid[button.value[0]][button.value[1]] == -1:
                    button.style = discord.ButtonStyle.red
                    button.label = "💣"
                button.disabled = True

        await self.views[0].update(content=f"`💀   🚩 {self.flags}   [Clicking]`")
        await self.views[1].update()

        await self.game_over()

    async def game_over(self):
        for view in self.views:
            button: Button
            for button in view.children:
                button.disabled = True
            await view.update()
            view.stop()

        self.views = None
        self.finished = True
