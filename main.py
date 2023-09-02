from dotenv import load_dotenv
import asyncio
import os
import io
import sys
from cogs.logging import get_logger
import openai
import openai.error
import discord
from discord.ext import commands
from discord import guild_only
import json
import wavelink
from cogs.DatabaseCog import DatabaseCog
from cogs.mockinteraction import MockInteraction

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
openai.api_key = os.getenv("OPENAI_API_KEY")
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
    node: wavelink.Node = wavelink.Node(uri='http://ash.lavalink.alexanderof.xyz:2333', password='lavalink',
                                        secure=False)
    await wavelink.NodePool.connect(client=bot, nodes=[node])
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='user commands'))
    for guild in bot.guilds:
        print(f"I'm active in {guild.id} a.k.a {guild}!")


@bot.slash_command(name="connect_nodes")
@guild_only()
async def connect_nodes(ctx):
    node: wavelink.Node = wavelink.Node(uri='http://ash.lavalink.alexanderof.xyz:2333', password='lavalink',
                                        secure=False)
    await wavelink.NodePool.connect(client=bot, nodes=[node])
    await bot.wait_until_ready()  # wait until the bot is ready
    await ctx.respond("Connected to lavalink node.")


async def shutdown(bot):
    await bot.close()


async def process_ssa_message(interaction, message):
    # Acknowledge the interaction if it exists
    try:
        if hasattr(interaction.response, 'defer'):
            await interaction.response.defer()
    except Exception as e:
        print(f"{e}")
        pass

    # Get the user id
    userid = "user"
    try:
        userid = str(interaction.message.author.id)
    except Exception as e:
        print(f"Error getting user id: {e}")
        pass

    db_cog.insert_chat_history(str(interaction.channel_id), userid, message)

    recent_messages = db_cog.fetch_recent_messages(str(interaction.channel_id), 30)
    messages = [{"role": "system", "content": json.dumps(db_cog.get_template("Second Shift Augie"))}]
    messages.extend([{"role": "user", "content": msg} for msg in recent_messages])
    messages.append({"role": "user", "content": json.dumps(message)})

    response = None
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
    except openai.error.APIError as e:
        # Handle API error here, e.g. retry or log
        print(f"OpenAI API returned an API Error: {e}")
        pass
    except openai.error.APIConnectionError as e:
        # Handle connection error here
        print(f"Failed to connect to OpenAI API: {e}")
        pass
    except openai.error.RateLimitError as e:
        # Handle rate limit error (we recommend using exponential backoff)
        print(f"OpenAI API request exceeded rate limit: {e}")
        pass

    content = response.choices[0].message.content
    if content:
        print(content)
        if len(content) > 2000:
            # Create a temporary file in memory
            with io.BytesIO(content.encode()) as f:
                # Send the content as a file
                await interaction.followup.send(file=discord.File(f, filename="response.txt"))
        else:
            await interaction.followup.send(f"{content}")
    else:
        await interaction.followup.send(f"I couldn't find an appropriate response for {message}.")


@bot.event
async def on_message(message):
    # If the bot is mentioned and the message isn't from the bot itself
    if bot.user in message.mentions and message.author != bot.user:
        # Store message in the database
        db_cog.insert_chat_history(message.channel.id, message.author.id, message.content)
        print(message.content)

        mock_interaction = MockInteraction(message)
        await process_ssa_message(mock_interaction, message.content.replace(f'<@!{bot.user.id}>', '').strip())
    else:
        if message.channel.type == discord.ChannelType.private and message.author != bot.user:
            print(f"Via DM: {message.content}")
            mock_interaction = MockInteraction(message)
            await process_ssa_message(mock_interaction, message.content.replace(f'<@!{bot.user.id}>', '').strip())

    await bot.process_commands(message)  # Ensure other commands are still processed


@bot.slash_command(name="ping", description="Sends the bot's latency.")  # this decorator makes a slash command
async def ping(ctx):  # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")


@bot.event
async def on_wavelink_node_ready(node: wavelink.Node) -> None:
    print(f"Node {node.id} is ready!")


@bot.slash_command(name="play")
async def play(ctx, search: str):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You must be in the same voice channel as the bot.")

    tracks = await wavelink.YouTubeTrack.search(search)
    if not tracks:
        await ctx.send(f'No tracks found with query: `{search}`')
        return

    track = tracks[0]
    await vc.play(track)
    await ctx.respond(f"Playing {tracks[0].title} by {tracks[0].author}")



if __name__ == '__main__':
    bot.load_extension("cogs.ssa")
    print("Connecting Wavelink Node")

    print("Done with Wavelink")

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
