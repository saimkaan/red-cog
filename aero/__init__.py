from .aero import Aero


def setup(bot):
    bot.add_cog(Aero(bot))