from .trainerdelay import TrainerDelay

async def setup(bot):
    await bot.add_cog(TrainerDelay(bot))
