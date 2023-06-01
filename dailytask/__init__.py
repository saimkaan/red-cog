from .test import DailyTask

async def setup(bot):
    await bot.add_cog(DailyTask(bot))
