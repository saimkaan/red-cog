from redbot.core import commands, Config
import datetime
import discord

class DailyMessage(commands.Cog):
    """A cog that posts a daily message to a Discord channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=198292929292)  # Replace identifier with a unique identifier for your cog
        self.config.register_guild(
            channel=None,
            message=None
        )

    @commands.group()
    async def daily(self, ctx):
        """Manage the daily message settings."""
        pass

    @daily.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        """Set the channel where the daily message will be posted."""
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Channel set to {channel.mention}.")

    @daily.command()
    async def message(self, ctx, *, message: str):
        """Set the message that will be posted daily."""
        await self.config.guild(ctx.guild).message.set(message)
        await ctx.send(f"Message set to {message}.")

    @commands.Cog.listener()
    async def on_ready(self):
        """Schedule the daily message task when the bot is ready."""
        await self.bot.wait_until_ready()
        self.bot.loop.create_task(self.daily_message_task())

    async def daily_message_task(self):
        """A task that runs every day and posts the daily message."""
        while not self.bot.is_closed():
            now = datetime.datetime.utcnow()
            if now.hour == 9 and now.minute == 1:  # 12:01 PST
                async with self.config.guild(self.bot.guilds[0]).all() as guild_config:
                    channel_id = guild_config["channel"]
                    message = guild_config["message"]
                    if channel_id and message:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send(message)
            await asyncio.sleep(60)  # wait for a minute before checking again
            print(now)
