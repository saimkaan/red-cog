from .test import DailyMessage

async def setup(bot):
    await bot.add_cog(DailyMessage(bot))
