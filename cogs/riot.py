import os
import re
import json
import requests
import urllib.parse
from datetime import timedelta
import modules.riot_tools as riot

import discord
from discord.ext import commands

JSON_PATH = "json/summoners.json"

class PaginationView(discord.ui.View):
    def __init__(self, skins: list, timeout: int = 180):
        super().__init__(timeout=timeout)
        self.index = 0
        self.skins = skins

    @discord.ui.button(label="<", style=discord.ButtonStyle.green, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index > 0:
            self.index -= 1
        else:
            self.index = len(self.skins) - 1
        
        await self.update_img(interaction=interaction)

    @discord.ui.button(label=">", style=discord.ButtonStyle.green, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.index < len(self.skins) - 1:
            self.index += 1
        else:
            self.index = 0

        await self.update_img(interaction=interaction)

    async def update_img(self, interaction: discord.Interaction):
        if not (img_data := requests.get(self.skins[self.index]['url']).content):
            raise Exception("Failed to get image.")

        img_name = self.skins[self.index]['url'].split("/")[-1]

        with open("downloads/" + img_name, "wb") as handler:
            handler.write(img_data)

        file = discord.File(fp="downloads/" + img_name)

        embed = discord.Embed(title=self.skins[self.index]['name'].title(), description="\t")
        embed.set_image(url="attachment://" + img_name)
        embed.set_footer(text=f"{self.index + 1}/{len(self.skins)}")

        await interaction.response.edit_message(embed=embed, attachments=[file])

        file.close()
        os.remove("downloads/" + img_name)

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
        
        async with ctx.channel.typing():
            summoner, member = tupl

            opgg_url = f"https://www.op.gg/summoners/na/{urllib.parse.quote(summoner['gameName'] + '-' + summoner['tagLine'])}"

            embed = discord.Embed(title=f"{summoner['gameName']} #{summoner['tagLine']}", description=f"**Level:** `{summoner['summonerLevel']}`" + " \u200b"*5 + f"**[OP.GG]({opgg_url})**")
            embed.set_thumbnail(url=riot.get_summoner_icon(summoner['profileIconId']))
            if member:
                embed.set_author(name=member.display_name, icon_url=member.display_avatar)

            # get ranked stats
            if stats := riot.get_stats_by_summoner(summoner['id']):
                for entry in [entry for entry in stats if "leagueId" in entry]:
                    embed.add_field(name=" ".join(entry['queueType'].split("_")[:-1]).title(), value=f"{entry['tier'].title()} {entry['rank']} `({entry['wins']}W|{entry['losses']}L)`")

            # get champion stats
            if masteries := riot.get_champion_masteries_by_puuid(summoner['puuid'], 3):
                for i, mastery in enumerate(masteries):
                    if not (champion := riot.get_champion_by_id(mastery['championId'])):
                        continue
                    if i == 0:
                        embed.add_field(name="\t", value="\t", inline=False)
                        embed.add_field(name="Highest Champion Mastery", value="\t", inline=False)

                    embed.add_field(name=champion['name'], value=f"Level: `{mastery['championLevel']}`\nPoints: `{mastery['championPoints']}`", inline=True)
            
            # get recent games
            if matchId := riot.get_matchId_by_puuid(summoner['puuid'], 3):
                def win_str(win: bool):
                    if win: return "\u001b[0;34m[W]\u001b[0;0m"
                    return "\u001b[0;31m[L]\u001b[0;0m"
                
                def time_str(duration: int):
                    return f"{str(timedelta(seconds=duration)).lstrip(':0')}"
                
                def pos_str(position: str):
                    if not position: return ""
                    if position == "UTILITY": return " (Support)"
                    return f" ({position.title()})"
                
                matches = list(filter(None, [riot.get_match_by_id(id) for id in matchId]))
                value = ""
                for matchDto in matches:
                    infoDto = matchDto['info']
                    participantDto = [participantDto for participantDto in infoDto['participants'] if participantDto['puuid'] == summoner['puuid']][0]
                    teamDto = [teamDto for teamDto in infoDto['teams'] if teamDto['teamId'] == participantDto['teamId']][0]

                    value += f"<t:{str(infoDto['gameCreation'] + infoDto['gameDuration']*1000)[:-3]}:R>\n"                                                                                  # {timestamp}
                    value += f"```ansi\n{win_str(participantDto['win'])} {infoDto['gameMode']} | "                                                                                          # {win/loss} {gamemode}
                    value += f"{participantDto['championName']}{pos_str(participantDto['teamPosition'])} | "                                                                                # {champion} {role}
                    value += f"{time_str(infoDto['gameDuration'])}\n"                                                                                                                       # {duration}
                    value += f"\u001b[0;36m{participantDto['kills']}/{participantDto['deaths']}/{participantDto['assists']}\u001b[0;0m "                                                    # {kda}
                    value += f"\u001b[0;30m({round(100 * (participantDto['kills'] + participantDto['assists']) / teamDto['objectives']['champion']['kills'])}%)\u001b[0;0m | "              # {kill participation}
                    value += f"CS: \u001b[0;36m{participantDto['totalMinionsKilled'] + participantDto['neutralMinionsKilled']}\u001b[0;0m"                                                  # {cs}
                    value += f"\u001b[0;30m({round(60 * (participantDto['totalMinionsKilled'] + participantDto['neutralMinionsKilled']) / infoDto['gameDuration'], 1)})\u001b[0;0m | "      # {cs/min}
                    value += f"Gold: \u001b[0;36m{participantDto['goldEarned']}\u001b[0;0m\n```"                                                                                            # {gold}
                
                embed.add_field(name="\t", value="\t", inline=False)
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
        
    @commands.hybrid_command(brief="View champion splash art.", description="View champion splash art.")
    async def splash(self, ctx: commands.Context, champion: str):
        if not (skins := riot.get_champion_skins_by_name(champion)):
            await error(ctx, "Champion not found.")
            return
        
        if not (img_data := requests.get(skins[0]['url']).content):
            await error(ctx, "Failed to get image.")
            return
        
        img_name = skins[0]['url'].split("/")[-1]

        with open("downloads/" + img_name, "wb") as handler:
            handler.write(img_data)

        file = discord.File(fp="downloads/" + img_name)
        
        embed = discord.Embed(title=skins[0]['name'].title(), description="\t")
        embed.set_image(url="attachment://" + img_name)
        embed.set_footer(text=f"1/{len(skins)}")

        await ctx.send(embed=embed, file=file, view=PaginationView(skins))

        file.close()
        os.remove("downloads/" + img_name)

async def error(ctx: commands.Context, description: str):
    embed = discord.Embed(title="Woops...", description=description)
    embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(RiotCog(bot))
    