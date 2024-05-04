from .pixelmondelay import PixelmonDelay

async def setup(bot):
    await bot.add_cog(PixelmonDelay(bot))
