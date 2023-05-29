from redbot.core import commands, Config, checks
from datetime import datetime, timedelta
from discord import Embed

class LastActivityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {"users": {}}
        self.config.register_global(**default_global)

    @commands.Cog.listener()
    async def on_message(self, message):
        author = message.author
        async with self.config.users() as users:
            users[str(author.id)] = datetime.now().timestamp()

    @commands.command()
    async def last_activity(self, ctx):
        embed = Embed(title="Users and their last activity time")
        users = await self.config.users()
        for user_id, last_activity in users.items():
            user = self.bot.get_user(int(user_id))
            if user:
                last_activity_time = datetime.fromtimestamp(last_activity)
                embed.add_field(name=user.name, value=last_activity_time)
            else:
                embed.add_field(name=f"User with ID {user_id}", value="Not found")
        await ctx.send(embed=embed)

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def kick_inactive(self, ctx):
        six_months_ago = datetime.now() - timedelta(days=180)
        users = await self.config.users()
        for user_id, last_activity in users.items():
            if datetime.fromtimestamp(last_activity) < six_months_ago:
                user = ctx.guild.get_member(int(user_id))
                if user:
                    await ctx.guild.kick(user)
                    await ctx.send(f"Kicked {user.name} for inactivity.")