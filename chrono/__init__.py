from .chrono import Chrono

async def setup(bot):
    await bot.add_cog(Chrono(bot))
