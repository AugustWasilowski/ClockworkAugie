from dotenv import load_dotenv
import asyncio
import os
import sys
from cogs import settings
from cogs.logging import get_logger
from cogs.queuehandler import GlobalQueue
import discord
from discord.ext import commands

from cogs.DatabaseCog import DatabaseCog

db_cog = DatabaseCog()

# Create the database table if it doesn't already exist
db_cog.create_table()

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot.logger = get_logger(__name__)
load_dotenv()
GUILD_ID = os.getenv("GUILD_ID")
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Discord bot token
CHANNEL_ID = os.getenv("CHANNEL_ID")  # Channel ID where SSA will log to.
VOICE_CHANNEL_ID = os.getenv("VOICE_CHANNEL_ID")
MOTD = "Second Shift Augie! Reporting for Duty!"

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    game = discord.Game("Use /ssa or /gpt4ci to interact.")
    await bot.change_presence(status=discord.Status.online, activity=game)
    channel = bot.get_channel(int(CHANNEL_ID))
    await channel.send(MOTD)

@bot.event
async def on_guild_join(guild):
    print(f'Wow, I joined {guild.name}!')


@bot.event
async def on_ready():
    bot.logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='user commands'))
    for guild in bot.guilds:
        print(f"I'm active in {guild.id} a.k.a {guild}!")


async def shutdown(bot):
    await bot.close()

@bot.event
async def on_message(message):
    # If the bot is mentioned and the message isn't from the bot itself
    if bot.user in message.mentions and message.author != bot.user:
        # Store message in the database
        db_cog.insert_chat_history(message.channel.id, message.author.id, message.content)
        print(message.content)

        ssa_instance = bot.get_cog("ssa")

        await ssa_instance.process_ssa_message(interaction,
           message=message.content.replace(f'<@!{bot.user.id}>', '').strip(), personality='Second Shift Augie')
    else:
        if message.channel.type == discord.ChannelType.private and message.author != bot.user:
            print(f"Via DM: {message.content}")
            ssa_instance = bot.get_cog("SSA")  # Get the SSA cog instance
            # Simulating the /ssa command behavior
            interaction = MockInteraction(message)
            await ssa_instance.process_ssa_message(interaction,
               message=message.content.replace(f'<@!{bot.user.id}>', '').strip(), personality='Second Shift Augie')

    await bot.process_commands(message)  # Ensure other commands are still processed

if __name__ == '__main__':
    try:
        bot.run(os.getenv("BOT_TOKEN"))
    except KeyboardInterrupt:
        bot.logger.info('Keyboard interrupt received. Exiting.')
        asyncio.run(shutdown(bot))
    except SystemExit:
        bot.logger.info('System exit received. Exiting.')
        asyncio.run(shutdown(bot))
    except Exception as e:
        bot.logger.error(e)
        asyncio.run(shutdown(bot))
    finally:
        sys.exit(0)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
