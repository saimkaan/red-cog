from redbot.core import commands, Config, checks
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from datetime import datetime, timedelta
from discord import Embed

class LastActivityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=187187187)
        default_global = {"users": {}}
        self.config.register_global(**default_global)
        self.users = {}

    async def load_users(self):
        self.users = await self.config.users()

    async def save_users(self):
        await self.config.users.set(self.users)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        author = message.author
        self.users[str(author.id)] = datetime.now().timestamp()
        await self.save_users()

    @commands.command()
    @checks.admin_or_permissions(administrator=True)
    async def kick_inactive(self, ctx):
        # Calculate the number of days of inactivity
        six_months_ago = datetime.now() - timedelta(days=180)
        days = (datetime.now() - six_months_ago).days

        # Kick members that have been inactive for the specified number of days
        count = await ctx.guild.prune_members(days=days, compute_prune_count=True)
        await ctx.send(f"Kicked {count} members for inactivity.")

    @commands.command()
    async def last_activity(self, ctx):
        users_per_page = 10
        pages = []
        users = list(self.users.items())
        for i in range(0, len(users), users_per_page):
            embed = Embed(title="Users and their last activity time")
            for user_id, last_activity in users[i:i+users_per_page]:
                user = self.bot.get_user(int(user_id))
                if user:
                    last_activity_time = datetime.fromtimestamp(last_activity)
                    embed.add_field(name=user.name, value=last_activity_time)
                else:
                    embed.add_field(name=f"User with ID {user_id}", value="Not found")
            pages.append(embed)
        await menu(ctx, pages, DEFAULT_CONTROLS)

    @commands.command()
    async def preview_kick(self, ctx):
        embed = Embed(title="Users that would be kicked by the kick_inactive command")
        # Calculate the number of days of inactivity
        six_months_ago = datetime.now() - timedelta(days=180)
        days = (datetime.now() - six_months_ago).days

        for user_id, last_activity in self.users.items():
            if (datetime.now() - datetime.fromtimestamp(last_activity)).days > days:
                user = self.bot.get_user(int(user_id))
                if user:
                    embed.add_field(name=user.name, value="Would be kicked")
                else:
                    embed.add_field(name=f"User with ID {user_id}", value="Not found")
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_red_ready(self):
        await self.load_users()
