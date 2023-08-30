import os
import io
import discord
from discord import option
from discord.ext import commands
import openai
import openai.error
import json
from cogs.DatabaseCog import DatabaseCog

db_cog = DatabaseCog()



class ssa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(ssa(bot))
    print("Loaded Second Shift Augie.")
