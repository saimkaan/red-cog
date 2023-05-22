from .headlinescog import HeadlinesCog

def setup(bot):
    bot.add_cog(HeadlinesCog(bot))

    # Make sure to return None or True at the end of the setup function
    return None
