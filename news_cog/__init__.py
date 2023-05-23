from .news_cog import NewsCog

def setup(bot):
    bot.add_cog(NewsCog(bot))
