import os
import io
from discord.ext import commands
from cogs.DatabaseCog import DatabaseCog

db_cog = DatabaseCog()



class ssa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(ssa(bot))
    print("Loaded Second Shift Augie.")
