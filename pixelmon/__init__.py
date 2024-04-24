from .pixelmon import Pixelmon

async def setup(bot):
    await bot.add_cog(Pixelmon(bot))
