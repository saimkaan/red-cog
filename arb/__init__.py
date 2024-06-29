from .arb import Arb

async def setup(bot):
    await bot.add_cog(Arb(bot))
