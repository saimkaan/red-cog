from redbot.core.bot import Red

from .headlinescog import HeadlinesCog


def setup(bot: Red):
    bot.add_cog(HeadlinesCog(bot))