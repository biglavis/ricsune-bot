import re
import json
import urllib.parse
from datetime import timedelta
import modules.riot_tools as riot

import discord
from discord.ext import commands

JSON_PATH = "json//summoners.json"

class RiotCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # load accounts
        try:
            with open(JSON_PATH, 'r') as f:
                self.db = json.load(f)
        except FileNotFoundError:
            self.db = {}

        print(f"cog: {self.qualified_name} loaded")

    @commands.hybrid_command(brief="Register your LoL account.", description="Register your LoL account.")
    async def register(self, ctx: commands.Context, *, riot_id: str):
        riot_id = riot_id.split("#")

        if len(riot_id) != 2:
            await error(ctx, "Invalid Riot ID.\nRiot ID must be in the form {gameName}#{tagLine}.")
            return

        if not (summoner := riot.get_summoner_by_name(riot_id[0], riot_id[1])):
            await error(ctx, "Account not found.")
            return

        self.db[str(ctx.author.id)] = summoner

        # save account
        with open(JSON_PATH, 'w') as f:
            json.dump(self.db, f, indent=4, default=str)

        await self.summoner(ctx)

    @commands.hybrid_command(brief="View summoner stats.", description="View summoner stats.")
    async def summoner(self, ctx: commands.Context, *, user: str = None):
        # get summoner
        if not (tupl := await self.get_summoner(ctx, user)):
            return
        
        summoner, member = tupl

        opgg_url = f"https://www.op.gg/summoners/na/{urllib.parse.quote(summoner['gameName'] + '-' + summoner['tagLine'])}"

        embed = discord.Embed(title=f"**{summoner['gameName']}#{summoner['tagLine']}**", description=f"**Level: **{summoner['summonerLevel']}" + " \u200b"*5 + f"**[OP.GG]({opgg_url})**")
        embed.set_thumbnail(url=riot.get_summoner_icon(summoner['profileIconId']))
        if member:
            embed.set_author(name=member.display_name, icon_url=member.display_avatar)

        # get ranked stats
        if stats := riot.get_stats_by_summoner(summoner['id']):
            for entry in [entry for entry in stats if "leagueId" in entry]:
                embed.add_field(name=" ".join(entry['queueType'].split("_")[:-1]).title(), value=f"{entry['tier'].title()} {entry['rank']} `({entry['wins']}W|{entry['losses']}L)`")
        
        # get recent games
        if matchId := riot.get_matchId_by_puuid(summoner['puuid'], 3):
            def win_str(win: bool):
                if win: return "W"
                return "L"
            
            def time_str(duration: int):
                return f"{str(timedelta(seconds=duration)).lstrip(':0')}"
            
            def pos_str(position: str):
                if not position: return ""
                if position == "UTILITY": return " (Support)"
                return f" ({position.title()})"
            
            matches = list(filter(None, [riot.get_match_by_matchId(id) for id in matchId]))
            value = ""
            for matchDto in matches:
                infoDto = matchDto['info']
                participantDto = [participantDto for participantDto in infoDto['participants'] if participantDto['puuid'] == summoner['puuid']][0]
                teamDto = [teamDto for teamDto in infoDto['teams'] if teamDto['teamId'] == participantDto['teamId']][0]

                value += f"<t:{str(infoDto['gameCreation'] + infoDto['gameDuration']*1000)[:-3]}:R>\n"
                value += f"```[{win_str(participantDto['win'])}] {infoDto['gameMode']} | {participantDto['championName']}{pos_str(participantDto['teamPosition'])} | {time_str(infoDto['gameDuration'])}\n"
                value += f"KDA: {participantDto['kills']}/{participantDto['deaths']}/{participantDto['assists']} ({round(100 * (participantDto['kills'] + participantDto['assists']) / teamDto['objectives']['champion']['kills'])}%) | "
                value += f"CS: {participantDto['totalMinionsKilled'] + participantDto['neutralMinionsKilled']}({round(60 * (participantDto['totalMinionsKilled'] + participantDto['neutralMinionsKilled']) / infoDto['gameDuration'], 1)}) | "
                value += f"Gold: {participantDto['goldEarned']}```"
            
            embed.add_field(name="Recent Games", value=value, inline=False)

        await ctx.send(embed=embed)

    async def get_summoner(self, ctx: commands.Context, user: str = None) -> tuple[dict, discord.Member] | None:
        if not user:
            if (id := str(ctx.author.id)) not in self.db:
                await error(ctx, "You are not registered.")
                return
    
            if not (summoner := riot.get_summoner_by_puuid(self.db[id]['puuid'])):
                await error(ctx, "Summoner not found.")
                return
            
            return summoner, ctx.author

        elif re.search(r"^[0-9]+$", user.strip("<@>")):
            if (id := user.strip("<@>")) not in self.db:
                await error(ctx, "User is not registered.")
                return
            
            if not (summoner := riot.get_summoner_by_puuid(self.db[id]['puuid'])):
                await error(ctx, "Summoner not found.")
                return
            
            return summoner, ctx.guild.get_member(int(id))
            
        elif len(riot_id := user.split("#")) == 2:
            if not (summoner := riot.get_summoner_by_name(riot_id[0], riot_id[1])):
                await error(ctx, "Summoner not found.")
                return
            
            return summoner, None

        else:
            await error(ctx, "Invalid user.\nUser must be a member or a Riot ID in the form {gameName}#{tagLine}.")
            return

async def error(ctx: commands.Context, description: str):
    embed = discord.Embed(title="Woops...", description=description)
    embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(RiotCog(bot))
    