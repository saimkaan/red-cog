from .kernyl import Kernyl


def setup(bot):
    bot.add_cog(Kernyl(bot))