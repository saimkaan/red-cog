from .lastactivitycog import LastActivityCog

async def setup(bot):
    await bot.add_cog(LastActivityCog(bot))
