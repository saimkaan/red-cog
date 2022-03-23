import discord
from redbot.core import commands

class Kernyl(commands.Cog):
    """My custom cog to troll Kernyl"""

    def __init__(self, bot):
        self.bot = bot
            
    @commands.Cog.listener()
    
    async def on_message(message):
        if len(message.content) > 250 or message.author.bot:
            return
        if message.channel.id === "944022733262569562":
            messageL = f"{message.author.name.replace(message.author.discriminator, '')} posted: '{message.content}'"
            success1 = await SendHomeMML(messageL)
        if success1 is None:
                print("Message Log message failed.")
            descE = f"{message.author.name.replace(message.author.discriminator, '')} posted: \n'{message.content}'\n" \
                f"This was in a Guild titled '{message.guild.name}' within Channel '{message.channel.name}'\n"
            MessageE = discord.Embed(title="Message Log", description=descE, colour=8421376)
            MessageE.set_footer(text=f"Posted on: {message.created_at.isoformat(' ')}")
            success2 = await SendHomeEML(MessageE)
            if success2 is None:
                print("Message Log embed failed.")
            # and so on...

    #Some time later... #

    async def SendHomeEML(embedded):
        return await bot.get_channel(956215619777359892).send(embed=embedded)

    async def SendHomeMML(message):
        return await bot.get_channel(956215619777359892).send(content=discord.utils.escape_mentions(message))
