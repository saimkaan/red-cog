from redbot.core import commands, Config
from datetime import datetime, timedelta
import discord
import asyncio

class DailyTask(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12300001312)
        default_guild = {
            "name": None,
            "channel": None,
            "message": None,
            "time": None,
            "days": None
        }
        self.config.register_guild(**default_guild)
        self.bg_task = self.bot.loop.create_task(self.my_background_task())

    async def my_background_task(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            all_guilds = await self.config.all_guilds()
            for guild_id in all_guilds:
                guild = self.bot.get_guild(guild_id)
                if guild is None:
                    continue
                message = await self.config.guild(guild).message()
                channel_id = await self.config.guild(guild).channel()
                channel = guild.get_channel(channel_id)
                if channel is None:
                    continue
                time_str = await self.config.guild(guild).time()
                if time_str is None:
                    continue
                post_time = datetime.strptime(time_str, '%H:%M').time()
                now = datetime.utcnow()
                if now.time() >= post_time:
                    days = await self.config.guild(guild).days()
                    if days is not None:
                        next_post_time = (now + timedelta(days=days)).replace(hour=post_time.hour, minute=post_time.minute)
                        await discord.utils.sleep_until(next_post_time)
                        await channel.send(message)
            await asyncio.sleep(60)

    @commands.group()
    @commands.guild_only()
    async def daily(self, ctx):
        pass

    @daily.command()
    async def task(self, ctx, name: str, message: str, channel: discord.TextChannel, days: int, *, time: str):
        try:
            datetime.strptime(time, '%H:%M')
        except ValueError:
            await ctx.send("Invalid time format. Please use HH:MM.")
            return
        await self.config.guild(ctx.guild).name.set(name)
        await self.config.guild(ctx.guild).message.set(message)
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await self.config.guild(ctx.guild).time.set(time)
        await self.config.guild(ctx.guild).days.set(days)
        await ctx.send("Task set.")

    @daily.command()
    async def list(self, ctx):
        name = await self.config.guild(ctx.guild).name()
        message = await self.config.guild(ctx.guild).message()
        channel_id = await self.config.guild(ctx.guild).channel()
        channel = ctx.guild.get_channel(channel_id)
        time_str = await self.config.guild(ctx.guild).time()
        days = await self.config.guild(ctx.guild).days()

        if not all([name, message, channel, time_str, days]):
            await ctx.send("Task not set up completely.")
            return

        embed = discord.Embed(title=name)
        embed.add_field(name="Message", value=message)
        embed.add_field(name="Channel", value=channel.mention)
        embed.add_field(name="Time", value=time_str)
        embed.add_field(name="Days", value=str(days))
        await ctx.send(embed=embed)
        
    @daily.command()
    async def delete(self, ctx, name: str):
        guild = ctx.guild
        task_name = await self.config.guild(guild).name()

        if task_name == name:
            await self.config.guild(guild).clear()
            await ctx.send(f"Task '{name}' has been deleted.")
        else:
            await ctx.send(f"No task with the name '{name}' found.")
