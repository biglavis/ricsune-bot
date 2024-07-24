import random
import discord
from discord.ext import commands

class TeamCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.participants = []
        print(f"cog: {self.qualified_name} loaded")

    @commands.hybrid_command(description="Create a new lobby from voice chat")
    async def make(self, ctx: commands.Context):
        if not ctx.author.voice:
            return

        self.participants = []
        for member in ctx.author.voice.channel.members:
            self.participants.append(member.mention)

        await self.lobby(ctx)

    @commands.hybrid_command(description="See who's in the lobby")
    async def lobby(self, ctx: commands.context):
        if not self.participants:
            description = "`/make` to create a new lobby from voice chat\n`/add` to add participants to a lobby"
            embed = discord.Embed(title="Your lobby is empty!", description=description)
            await ctx.send(embed=embed)
            return

        description = ""
        for i, member in enumerate(self.participants):
            description += f"`[{i+1}]` {member}\n"

        description += "\n`/add {name}` to add a participant"
        description += "\n`/kick {id}` to remove a participant"
        description += "\n`/teams {x}` to create x random teams"
        description += "\n`/destroy` to destroy this lobby"
    
        embed = discord.Embed(title="Participants", description=description)
        await ctx.send(embed=embed, silent=True) 

    @commands.hybrid_command(description="Add a participant to the lobby")
    async def add(self, ctx: commands.context, name: str):
        self.participants.append(name)
        embed = discord.Embed(description=f"Added {name} to the lobby")
        embed.set_footer(text="/lobby to see who's in the lobby")
        await ctx.send(embed=embed, silent=True) 

    @commands.hybrid_command(description="Kick a participant from the lobby")
    async def kick(self, ctx: commands.context, id: int):
        if not self.participants:
            return
        if id < 1 or id > len(self.participants):
            return
        
        member = self.participants.pop(id-1)
        embed = discord.Embed(description=f"Kicked {member} from the lobby")
        embed.set_footer(text="/lobby to see who's in the lobby")
        await ctx.send(embed=embed, silent=True) 

    @commands.hybrid_command(description="Create x random teams")
    async def teams(self, ctx: commands.context, x: int):
        if not self.participants:
            description = "`/make` to create a new lobby from voice chat\n`/add` to add participants to a lobby"
            embed = discord.Embed(title="Your lobby is empty!", description=description)
            await ctx.send(embed=embed)
            return
        
        if x < 1:
            await error(ctx, "Too few teams!")
            return
        
        if x > len(self.participants):
            await error(ctx, "Too many teams!")
            return 
        
        participants = random.sample(self.participants, len(self.participants))

        embed = embed = discord.Embed(title="Teams")

        for i in range(x):
            value = ""
            for member in participants[round(len(participants)/x*i):round(len(participants)/x*(i+1))]:
                value += f"{member}\n"
            embed.add_field(name=f"Team {i+1}", value=value)

        await ctx.send(embed=embed, silent=True)

    @commands.hybrid_command("Destroy the current lobby")
    async def destroy(self, ctx: commands.context):
        if not self.participants:
            return
        
        self.participants = []

        description = "`/make` to create a new lobby from the active voice chat\n`/add` to add participants to a lobby"
        embed = discord.Embed(title="Lobby destroyed!", description=description) 
        await ctx.send(embed=embed)

async def error(ctx: commands.Context, description: str):
    embed = discord.Embed(title="Woops...", description=description)
    embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.avatar)
    await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TeamCog(bot))
