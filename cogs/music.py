import os
from datetime import timedelta
import yt_dlp

import discord
from discord.ext import commands

MAX_SEARCH = 5
YDL_OPTS = {
    'format': 'm4a/bestaudio/best',
    'outtmpl': './downloads/%(id)s.%(ext)s',
    'match_filter': yt_dlp.utils.match_filter_func("original_url!*=/shorts/ & url!*=/shorts/"),
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'extract_flat': True,
    'no_warnings': True,
    'quiet': True
}

def parse(duration: int):
    return f"{str(timedelta(seconds=duration)).lstrip(':0')}"

class MusicCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = []
        self.now_playing = None
        print(f"cog: {self.qualified_name} loaded")

    @commands.hybrid_command(brief="Add a song to the queue.", description="Add a song to the queue.")
    async def play(self, ctx: commands.Context, *, song: str):
        if not (ctx.guild.voice_client in self.bot.voice_clients or ctx.author.voice):
            await error(ctx, "You are not in a voice channel.")
            return
    
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            # grab link
            if any(site in song for site in ["youtube.com/", "youtu.be/"]):
                video = ydl.extract_info(f"ytsearch:{song}", download=False)['entries'][0]

            # search for video
            else:
                videos = ydl.extract_info(f"ytsearch{MAX_SEARCH}:{song}", download=False)['entries']

                # list search results
                description = ""
                for i, video in enumerate(videos):
                    description += f"`[{i+1}]` [{video['title']}]({video['url']}) ({parse(video['duration'])})\n"

                embed = discord.Embed(title="Search Results:", description=description)
                embed.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.guild_avatar)

                await ctx.send(embed=embed)

                # wait for response
                def check(m: discord.Message): # checking if it's the same user and channel
                    return m.author == ctx.author and m.channel == ctx.channel

                try:
                    response = await self.bot.wait_for('message', check=check, timeout=30.0)
                    index = int(response.content) - 1
                except:
                    return
                
                if index < 0 or index > len(videos) - 1:
                    return
                
                video = videos[index]

            # grab metadata
            url, title, duration, id = video['url'], video['title'], video['duration'], video['id']
            thumbnail = sorted(video['thumbnails'], key = lambda x: x['height'])[0]['url']
            user = ctx.author.display_name

            # add to queue
            loc = locals()
            self.queue.append({i: loc[i] for i in ('url', 'title', 'duration', 'thumbnail', 'id', 'user')})

            embed = discord.Embed(description=f"Added **[{title}]({url}) ({parse(duration)})** to the queue")
            embed.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.guild_avatar)

            await ctx.send(embed=embed)

            # start playing
            if ctx.guild.voice_client not in self.bot.voice_clients:
                await ctx.author.voice.channel.connect()
            if not ctx.voice_client.is_playing():
                await self.play_next(ctx)

    async def play_next(self, ctx: commands.Context):
        # flush downloads
        if os.path.exists("./downloads"):
            for file in os.listdir("./downloads"):
                os.remove(f"./downloads/{file}")
    
        if self.queue:
            self.now_playing = self.queue.pop(0)

            # download audio
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                ydl.extract_info(self.now_playing['url'])

            # play
            ctx.voice_client.play(discord.FFmpegPCMAudio(f"./downloads/{self.now_playing['id']}.m4a"), after=lambda _: self.bot.loop.create_task(self.play_next(ctx)))

        else:
            self.now_playing = None

    @commands.hybrid_command(brief="See what's playing.", description="See what's playing.")
    async def playing(self, ctx: commands.Context):
        if not self.now_playing:
            embed = discord.Embed(title="Nothing is playing!", description="Add a song with `/play`")
            await ctx.send(embed=embed)
            return

        description = f"**[{self.now_playing['title']}]({self.now_playing['url']})**\n"
        description += f"**({parse(self.now_playing['duration'])})** \u00B7 Requested by {self.now_playing['user']}"
        embed = discord.Embed(title="Now Playing", description=description)
        embed.set_thumbnail(url=self.now_playing['thumbnail'])
        runtime = self.now_playing['duration']

        if self.queue:
            value = ""
            for i, song in enumerate(self.queue):
                value += f"`[{i+1}]` [{song['title']}]({song['url']}) ({parse(song['duration'])})\n"
                runtime += song['duration']
        else:
            value = "Queue is empty\n"
        value += "\nAdd a song with `/play`"
        embed.add_field(name="Next Up:", value=value, inline=False)

        embed.set_footer(text=f"{len(self.queue)+1} Tracks" + " \u200b"*3 + f"({parse(runtime)})")

        await ctx.send(embed=embed)

    @commands.hybrid_command(brief="Skip the current song.", description="Skip the current song.")
    async def skip(self, ctx: commands.Context):
        if not (ctx.guild.voice_client in self.bot.voice_clients and ctx.voice_client.is_playing()):
            return
        
        embed = discord.Embed(description=f"Skipped **[{self.now_playing['title']}]({self.now_playing['url']}) ({parse(self.now_playing['duration'])})**")
        embed.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.guild_avatar)

        await ctx.send(embed=embed)

        ctx.voice_client.stop()

    @commands.hybrid_command(brief="Mic drop.", description="Mic drop.")
    async def stop(self, ctx: commands.Context):
        self.queue = []
        if ctx.guild.voice_client in self.bot.voice_clients:
            await ctx.voice_client.disconnect()
    
async def error(ctx: commands.Context, description: str):
    if not (avatar := ctx.author.guild_avatar):
        avatar = ctx.author.avatar
    embed = discord.Embed(title="Woops...", description=description)
    embed.set_footer(text=ctx.author.display_name, icon_url=avatar)
    await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
    