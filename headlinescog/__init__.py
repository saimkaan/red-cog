from redbot.core.bot import Red

from .headlinescog import HeadlinesCog


def setup(bot: Red):
    cog = HeadlinesCog(bot)
    bot.add_cog(cog)
