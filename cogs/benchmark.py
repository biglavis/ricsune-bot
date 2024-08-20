import random

import discord
from discord.ext import commands

class Button(discord.ui.Button):
    def __init__(self, view_subclass = None, label: str = "\u200b", custom_id: str = None):
        super().__init__(label=label, style=discord.ButtonStyle.grey, custom_id=custom_id)
        self.value = None

    async def callback(self, interaction: discord.Interaction):
        view: ChimpView = self.view
        await view.interacted(button=self, interaction=interaction)

class ChimpView(discord.ui.View):
    def __init__(self, timeout: int = 180):
        super().__init__(timeout=timeout)
        for i in range(25):
            self.add_item(Button(custom_id=f"button_{i}"))
        self.stage = 4

        self.scramble()

    def scramble(self):
        values = list(range(1, self.stage+1)) + [None] * (25 - self.stage)
        random.shuffle(values)
        
        button: Button
        for i, button in enumerate(self.children):
            button.value = values[i]

        self.reveal()

    def reveal(self):
        button: Button
        for button in self.children:
            if button.value:
                button.style = discord.ButtonStyle.blurple
                button.label = str(button.value)

    def hide(self):
        button: Button
        for button in self.children:
            button.style = discord.ButtonStyle.grey
            button.label = "\u200b"

    async def interacted(self, button: discord.ui.Button, interaction: discord.Interaction):
        button.style = discord.ButtonStyle.red
        button.label = "\u200b"

        await interaction.response.edit_message(view=self)

class BenchmarkCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print(f"cog: {self.qualified_name} loaded")

    @commands.command()
    async def chimp(self, ctx: commands.Context):
        await ctx.send(view=ChimpView())

async def setup(bot: commands.Bot):
    await bot.add_cog(BenchmarkCog(bot))
