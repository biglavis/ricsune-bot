import os
from dotenv import load_dotenv
from modules.chat_tools import ask_sydney

import discord
from discord.ext import commands

class ChatCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        print(f"cog: {self.qualified_name} loaded")

    @commands.hybrid_command(description='Ask Microsoft Copilot.')
    async def ask(self, ctx: commands.Context, *, prompt: str):
        async with ctx.channel.typing(): 
            image, response = await ask_sydney(prompt)
            
            # reply
            embed = discord.Embed(description=f'> {prompt} \n\n' + response)

            if image != None:
                embed.set_image(url=image)

            icon = discord.File('assets/Copilot.png') 
            embed.set_author(name='Microsoft Copilot', icon_url = 'attachment://Copilot.png')
            embed.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.avatar)
            await ctx.send(file=icon, embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatCog(bot))