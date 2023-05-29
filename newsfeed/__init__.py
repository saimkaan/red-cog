from .newsfeed import NewsFeed

async def setup(bot):
    await bot.add_cog(NewsFeed(bot))
