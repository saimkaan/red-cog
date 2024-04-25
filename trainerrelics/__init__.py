from .trainerrelics import TrainerRelics

async def setup(bot):
    await bot.add_cog(TrainerRelics(bot))
