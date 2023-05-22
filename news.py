import discord
from discord.ext import commands, tasks
import requests

API_URL = 'https://phx.unusualwhales.com/api/news/headlines-feed?limit=50'

class HeadlinesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.posted_headlines = set()
        self.check_headlines.start()

    def cog_unload(self):
        self.check_headlines.cancel()

    @tasks.loop(seconds=5.0)
    async def check_headlines(self):
        latest_headlines = self.get_latest_headlines()
        channel = self.bot.get_channel(YOUR_CHANNEL_ID)
        for headline in latest_headlines:
            headline_id = headline['id']
            if headline_id not in self.posted_headlines:
                self.posted_headlines.add(headline_id)
                await channel.send(headline['headline'])

    def get_latest_headlines(self):
        response = requests.get(API_URL)
        if response.status_code == 200:
            data = response.json()
            if data and 'results' in data:
                return data['results']
        return []

    @commands.command()
    async def start_headlines(self, ctx):
        self.check_headlines.start()
        await ctx.send("Started posting the latest headlines.")

    @commands.command()
    async def stop_headlines(self, ctx):
        self.check_headlines.stop()
        await ctx.send("Stopped posting the latest headlines.")

    @commands.command()
    async def restart_headlines(self, ctx):
        self.check_headlines.restart()
        await ctx.send("Restarted posting the latest headlines.")

def setup(bot):
    bot.add_cog(HeadlinesCog(bot))