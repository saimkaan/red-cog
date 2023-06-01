from redbot.core import commands, Config
import datetime
import discord
import asyncio


class DailyMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=198292929292)
        self.config.register_guild(
            channel=None,
            message=None,
            last_posted=None
        )
        self.daily_message_task = None

    @commands.group()
    async def daily(self, ctx):
        pass

    @daily.command()
    async def channel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Channel set to {channel.mention}.")

    @daily.command()
    async def message(self, ctx, *, message: str):
        await self.config.guild(ctx.guild).message.set(message)
        await ctx.send(f"Message set to {message}.")

    @daily.command()
    async def start(self, ctx):
        if self.daily_message_task:
            await ctx.send("Daily message task has already been started.")
        else:
            self.daily_message_task = self.bot.loop.create_task(self._daily_message_task(ctx))
            await ctx.send("Daily message task has been started.")

    @daily.command()
    async def list(self, ctx):
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

    async def _daily_message_task(self, ctx):
        while not self.bot.is_closed():
            now = datetime.datetime.utcnow()
            if now.hour == 7 and now.minute == 1 and self._should_post_message(ctx.guild):
                await self._post_daily_message(ctx.guild)
            await asyncio.sleep(60)

    async def _post_daily_message(self, guild):
        async with self.config.guild(guild).all() as guild_config:
            channel_id = guild_config["channel"]
            message = guild_config["message"]
            guild_config["last_posted"] = datetime.datetime.utcnow().date().isoformat()
        if channel_id and message:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(message)

    def _should_post_message(self, guild):
        last_posted = self.config.guild(guild).last_posted()
        today = datetime.datetime.utcnow().date().isoformat()
        return last_posted != today

    def cog_unload(self):
        if self.daily_message_task:
            self.daily_message_task.cancel()
