from .relics import Relics

async def setup(bot):
    await bot.add_cog(Relics(bot))
