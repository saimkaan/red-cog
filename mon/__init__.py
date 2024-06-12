from .mon import Mon

async def setup(bot):
    await bot.add_cog(Mon(bot))
