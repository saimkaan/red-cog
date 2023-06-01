from redbot.core import commands
from redbot.core import Config
import datetime
import discord

class DailyMessage(commands.Cog):
    """A cog that posts a daily message to a Discord channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=198762736482, force_registration=True)
        default_global = {"channel": None, "message": None}
        self.config.register_global(**default_global)


    @commands.group()
    async def daily(self, ctx):
        """Manage the daily message settings."""
        pass

    @daily.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where the daily message will be posted."""
        await self.config.channel.set(channel.id)
        await ctx.send(f"Channel set to {channel.mention}.")

    @daily.command()
    async def message(self, ctx, *, message: str):
        """Set the message that will be posted daily."""
        await self.config.message.set(message)
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
                channel_id = await self.config.channel()
                message = await self.config.message()
                if channel_id and message:
                    channel = self.bot.get_channel(channel_id)
                    await channel.send(message)
            await asyncio.sleep(60) # wait for a minute before checking again
