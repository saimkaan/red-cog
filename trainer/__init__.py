from .trainer import Trainer

async def setup(bot):
    await bot.add_cog(Trainer(bot))