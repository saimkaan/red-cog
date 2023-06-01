from redbot.core import commands
import datetime
import discord

class DailyMessage(commands.Cog):
    """A cog that posts a daily message to a Discord channel."""

    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.message = None

    @commands.group()
    async def daily(self, ctx):
        """Manage the daily message settings."""
        pass

    @daily.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where the daily message will be posted."""
        self.channel = channel
        await ctx.send(f"Channel set to {channel.mention}.")

    @daily.command()
    async def message(self, ctx, *, message: str):
        """Set the message that will be posted daily."""
        self.message = message
        await ctx.send(f"Message set to {message}.")

    @commands.Cog.listener()
    async def on_ready(self):
        """Schedule the daily message task when the bot is ready."""
        self.bot.loop.create_task(self.daily_message_task())

    async def daily_message_task(self):
    """A task that runs every day and posts the daily message."""
    await self.bot.wait_until_ready()
    while not self.bot.is_closed():
        now = datetime.datetime.utcnow()
        print(now)
        if now.hour == 9 and now.minute == 1: # 09:01 bot time
            if self.channel and self.message:
                await self.channel.send(self.message)
        await asyncio.sleep(60) # wait for a minute before checking again
