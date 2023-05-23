
from .headlinescog import HeadlinesCog


async def setup(bot):
    cog = HeadlinesCog(bot)
    bot.add_cog(cog)
