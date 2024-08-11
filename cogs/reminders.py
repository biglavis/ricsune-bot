import json
import re
import datetime
from datetime import timedelta
from modules.reminder_tools import parse_time

import discord
from discord.ext import commands, tasks

JSON_PATH = 'json//reminders.json'

def date_hook(json_dict):
    for (key, value) in json_dict.items():
        try:
            json_dict[key] = datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S%z")
        except:
            pass
    return json_dict

class ReminderCog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # load reminders
        try:
            with open(JSON_PATH, 'r') as f:
                self.db = json.load(f, object_hook=date_hook)
        except FileNotFoundError:
            self.db = {}

        # remove expired reminders
        now = datetime.datetime.now(datetime.timezone.utc).astimezone()
        for id in self.db:
            expired = [reminder for reminder in self.db[id]['reminders'] if reminder['time'] <= now]
            for reminder in expired:
                self.db[id]['reminders'].remove(reminder)

        # save reminders
        with open(JSON_PATH, 'w') as f:
            json.dump(self.db, f, indent=4, default=str)

        # start reminding
        self.remind.start()
        
        print(f'cog: {self.qualified_name} loaded')

    def add_user(self, id: int):
        self.db[str(id)] = {'reminders': []}
        with open(JSON_PATH, 'w') as f:
            json.dump(self.db, f, indent=4, default=str)

    @commands.hybrid_command(brief='Set a reminder.', description='Set a reminder.')
    async def remindme(self, ctx: commands.Context, *, string: str = ""):
        
        id = ctx.author.id
        now = ctx.message.created_at.astimezone().replace(microsecond=0)
        url = ctx.message.jump_url

        # add user if user not in database
        if str(id) not in self.db:
            self.add_user(id)

        user = self.db[str(id)]

        # parse reminder
        try:
            time, task = parse_time(string, now)
        except:
            examples = ("/remindme in 2h30m drink water\n"
                        "/remindme at 5pm on sept 21\n"
                        "/remindme thursday at 3:45 do laundry\n"
                        "/remindme on january 6 2021 raid capitol\n"
                        "/remindme tmr 8am kiss the homies\n")

            units = ("```y : years | mo : months | w : weeks | d : days\n"
                     "h : hours | m : minutes | s : seconds```"
                    )

            embed = discord.Embed(title="Woops...", description="Invalid syntax.")
            embed.add_field(name="Pre (Optional)", value="in?\nat?\non?\non?", inline=True)
            embed.add_field(name="When (Required)", value="{amount}{units}\n{time}\n{month}{day}{year}?\n{weekday}", inline=True)
            embed.add_field(name="What (Optional)", value="{task}?\n{task}?\n{task}?\n{task}?", inline=True)
            embed.add_field(name="Examples", value=examples, inline=False)
            embed.add_field(name="Units", value=units, inline=False)
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            
            await ctx.send(embed=embed)
            return
        
        if time <= now:
            await error(ctx, "I cannot work backwards... maybe one day.")
            return

        # add reminder
        user['reminders'].append({'time': time, 'task': task, 'url': url, 'created': now, 'modified': now})

        # sort reminders by time
        user['reminders'] = sorted(user['reminders'], key=lambda x: x['time'])

        # save reminders
        with open(JSON_PATH, 'w') as f:
            json.dump(self.db, f, indent=4, default=str)

        # reply
        reply = f'I will remind you **<t:{round(time.timestamp())}:R>**'
        if task != "":
            reply += f'\n> *{task}*'

        embed = discord.Embed(title="Reminder Set", description=reply)
        embed.set_footer(text=f"{ctx.author.display_name} \u00B7 /rm to delete this reminder", icon_url=ctx.author.display_avatar)

        await ctx.send(embed=embed)

    @commands.hybrid_command(brief='List your reminders.', description='List your reminders.')
    async def reminders(self, ctx: commands.Context):

        id = ctx.author.id

        # add user if user not in database
        if str(id) not in self.db:
            self.add_user(id)

        user = self.db[str(id)]

        # reply
        if len(user['reminders']) == 0:
            embed = discord.Embed(title="Your Reminders:", description="You have no reminders.")
        else:
            description = ""
            for i, reminder in enumerate(user['reminders']):
                description += f'`[{i+1}]` | **<t:{round(reminder["time"].timestamp())}:R>**\n'
                if reminder["task"] != "":
                    description = description[:-1] + " \u200b"*5 + f'**>** *{reminder["task"]}*\n'

            embed = discord.Embed(title="Your Reminders:", description=description)

        embed.add_field(name="\u200b", value="`/info {index}` to get information about a reminder.\n`/rm {indexes}` to delete reminder(s).\n`/rm all` to delete all reminders.")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar)

        await ctx.send(embed=embed)

    @commands.hybrid_command(brief='Get information about a reminder.', description='Get information about a reminder.')
    async def info(self, ctx: commands.Context, index: int = None):

        id = ctx.author.id
        now = ctx.message.created_at.astimezone().replace(microsecond=0)

        # add user if user not in database
        if str(id) not in self.db:
            self.add_user(id)
            
        user = self.db[str(id)]

        # if user has no reminders
        if len(user['reminders']) == 0:
            await error(ctx, "You have no reminders.")
            return 
        
        # get recent
        if index == None:
            recent = sorted(user['reminders'], key=lambda x: x['modified'])[-1]

            if now - recent['modified'] < timedelta(minutes=3):
                index = user['reminders'].index(recent) + 1
            else:
                await error(ctx, "Reminder not found.")
                return 
        
        # if invalid index
        elif abs(index) > len(user['reminders']):
            await error(ctx, "Invalid index.")
            return
        
        # get reminder
        reminder = user['reminders'][abs(index)-1]

        # update modified
        user['reminders'][abs(index)-1]['modified'] = now
        
        # save reminders
        with open(JSON_PATH, 'w') as f:
            json.dump(self.db, f, indent=4, default=str)

        # reply
        reply = f'on **{reminder["time"].strftime("%b %d, %Y")}** at **{reminder["time"].strftime("%I:%M %p")}** \u00B7 <t:{round(reminder["time"].timestamp())}:R>\n'

        if reminder['task'] != "":
            reply += f'> *{reminder["task"]}*\n'
        else: 
            reply += f'> *<empty>*\n'

        reply += f'\n**ID**: `[{abs(index)}]`'
        
        embed = discord.Embed(title="Reminder", description=reply)
        embed.add_field(name="Created", value=f'<t:{round(reminder["created"].timestamp())}:R>', inline=False)
        embed.add_field(name="Original Message", value=reminder['url'], inline=False)
        embed.set_footer(text=f'{ctx.author.display_name} \u00B7 /rm to delete this reminder', icon_url=ctx.author.display_avatar) 

        await ctx.send(embed=embed)

    @commands.hybrid_command(brief='Delete reminder(s).', description='/rm {indexes} to delete reminder(s). /rm {all} to clear all reminders.')
    async def rm(self, ctx: commands.Context, *, indexes: str = None):

        id = ctx.author.id
        now = ctx.message.created_at.astimezone().replace(microsecond=0)

        # add user if user not in database
        if str(id) not in self.db:
            self.add_user(id)

        user = self.db[str(id)]

        # if user has no reminders
        if len(user['reminders']) == 0:
            await error(ctx, "You have no reminders.")
            return
        
        # delete recent
        elif indexes == None:
            recent = sorted(user['reminders'], key=lambda x: x['modified'])[-1]

            if now - recent['modified'] < timedelta(minutes=3):
                indexes = [user['reminders'].index(recent) + 1]
            else:
                await error(ctx, "Reminder not found.")
                return 

        # delete all
        elif matched := re.search(r"all", indexes):
            indexes = list(range(1, len(user['reminders']) + 1))

        # delete indexed
        elif matched := re.findall(r"\d+", indexes):
            indexes = [int(i) for i in matched if int(i) <= len(user['reminders'])]
            indexes.sort()

        # if invalid index
        else:
            await error(ctx, "Invalid index.")
            return
        
        if len(indexes) == 0:
            await error(ctx, "Invalid index.")
            return
        
        # get reminders
        reminders = [user['reminders'][(i-1)] for i in indexes]
        
        # delete reminders
        for reminder in reminders:
            user['reminders'].remove(reminder)

        # save reminders
        with open(JSON_PATH, 'w') as f:
            json.dump(self.db, f, indent=4, default=str)

        # reply
        description = ""
        for i, reminder in zip(indexes,reminders):
            description += f'> `[{i}]` | **<t:{round(reminder["time"].timestamp())}:R>**\n'
            if reminder["task"] != "":
                description = description[:-1] + " \u200b"*5 + f'**>** *{reminder["task"]}*\n'

        embed = discord.Embed(title="Reminders Deleted", description=description)
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)

        await ctx.send(embed=embed)

    @tasks.loop(seconds=5)
    async def remind(self):
        now = datetime.datetime.now(datetime.timezone.utc).astimezone()

        # reminders are sorted by time
        # for each user, check top reminder
        for id in self.db:
            if len(self.db[id]['reminders']) == 0:
                pass
            else:
                reminder = self.db[id]['reminders'][0]

                if reminder['time'] <= now:
                    author = await self.bot.fetch_user(int(id))

                    if reminder['task'] != "":
                        embed = discord.Embed(title="Reminder", description=f'> *{reminder["task"]}*', timestamp=reminder["created"])
                    else:
                        embed = discord.Embed(title="Reminder", timestamp=reminder["created"])

                    embed.add_field(name="Original Message", value=reminder['url'])
                    embed.set_footer(text=f'{author.display_name}', icon_url=author.display_avatar)

                    # send reminder
                    await author.send(embed=embed)

                    # delete reminder
                    self.db[id]['reminders'].remove(reminder)

                    # save reminders
                    with open(JSON_PATH, 'w') as f:
                        json.dump(self.db, f, indent=4, default=str)

    @remind.before_loop
    async def before_remind(self):
        await self.bot.wait_until_ready()

async def error(ctx: commands.Context, description: str):
    embed = discord.Embed(title="Woops...", description=description)
    embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReminderCog(bot))
    