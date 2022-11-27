import discord
from redbot.core import commands

class Aero(commands.Cog):
    """My custom cog"""

    def __init__(self, bot):
        self.bot = bot
            
    @commands.command(aliases=["lastseen"])
    async def all_members(ctx):
    await ctx.send(ctx.guild.members)
