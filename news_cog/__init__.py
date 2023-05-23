from .news_cog import NewsCog

async def setup(bot):
    await bot.add_cog(NewsCog(bot))
