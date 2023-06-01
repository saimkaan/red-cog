from redbot.core import commands, Config
import datetime
import discord
import asyncio


class DailyMessage(commands.Cog):
    """A cog that posts a daily message to a Discord channel."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=198292929292)  # Replace identifier with a unique identifier for your cog
        self.config.register_guild(
            channel=None,
            message=None,
            days_remaining=None
        )
        self.task_started = False

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

    @daily.command()
    async def start(self, ctx):
        """Start the daily message task."""
        if self.task_started:
            await ctx.send("Daily message task has already been started.")
        else:
            await self.config.guild(ctx.guild).days_remaining.set(30)
            await self.daily_message_task(ctx)
            await ctx.send("Daily message task has been started.")
            self.task_started = True

    @daily.command()
    async def list(self, ctx):
        """List all the daily messages along with their channel and message info."""
        async with self.config.guild(ctx.guild).all() as guild_config:
            channel_id = guild_config["channel"]
            message = guild_config["message"]
        if channel_id and message:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(title="Daily Message List", color=discord.Color.blue())
                embed.add_field(name="Channel", value=channel.mention, inline=False)
                embed.add_field(name="Message", value=message, inline=False)
                await ctx.send(embed=embed)
        else:
            await ctx.send("No daily message has been set.")

    async def daily_message_task(self, ctx):
        """A task that runs every day and posts the daily message."""
        while not self.bot.is_closed():
            now = datetime.datetime.utcnow()
            if now.hour == 9 and now.minute == 1:  # 12:01 PST
                async with self.config.guild(ctx.guild).all() as guild_config:
                    channel_id = guild_config["channel"]
                    message = guild_config["message"]
                    days_remaining = guild_config["days_remaining"]
                    if channel_id and message and days_remaining > 0:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send(message)
                            days_remaining -= 1
                            await self.config.guild(ctx.guild).days_remaining.set(days_remaining)
            await asyncio.sleep(60)  # wait for a minute before checking again
