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
from wavelink import TrackEventPayload
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
players = {}
current_tracks = {}  # Dictionary to store track_id for each guild



@bot.event
async def on_guild_join(guild):
    print(f'Second Shift Augie joined {guild.name}!')


@bot.event
async def on_ready():
    channel = bot.get_channel(int(CHANNEL_ID))
    await channel.send(MOTD)
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


@bot.slash_command(name="ping", description="Sends the bot's latency.")
async def ping(ctx):
    latency_ms = round(bot.latency * 1000)  # Convert latency to milliseconds
    await ctx.respond(f"Pong! Latency is {latency_ms}ms")



@bot.event
async def on_wavelink_node_ready(node: wavelink.Node) -> None:
    print(f"Node {node.id} is ready!")


@bot.event
async def on_wavelink_track_end(payload: TrackEventPayload) -> None:
    guild_id = payload.player.guild

    # Ensure the guild_id is associated with a list
    if guild_id not in current_tracks or not isinstance(current_tracks[guild_id], list):
        current_tracks[guild_id] = []

    # Pop the first track ID from the list if it's not empty
    track_id = current_tracks[guild_id].pop(0) if current_tracks[guild_id] else None

    if track_id:
        db_cog.remove_played_track(track_id)

    if not current_tracks.get(guild_id):
        del current_tracks[guild_id]

    vc: wavelink.Player = payload.player

    next_track_info = db_cog.fetch_next_track(payload.player.channel.id)
    if next_track_info:
        track_id, title, author, link = next_track_info  # Extract the track_id from the next_track_info
        current_tracks[guild_id] = track_id  # Update the track_id in current_tracks dictionary
        next_track = await wavelink.YouTubeTrack.search(link)
        if next_track:
            print(f"Playing {title} by {author} next...")
            await vc.play(next_track[0])



@bot.slash_command(name="showqueue")
async def showqueue(ctx):
    queue = db_cog.fetch_all_tracks(ctx.channel.id)
    if not queue:
        return await ctx.respond("The queue is currently empty.")

    tracks_list = []
    for idx, (_, title, author, _) in enumerate(queue, 1):
        tracks_list.append(f"{idx}. {title} by {author}")

    message = "\n".join(tracks_list)

    await ctx.respond(message)


@bot.slash_command(name="nextsong")
async def nextsong(ctx):
    guild_id = ctx.guild.id

    if guild_id not in players:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        players[guild_id] = vc  # Store the player instance in the dictionary
    else:
        vc = players[guild_id]

    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You must be in the same voice channel as the bot.")

    next_track_info = db_cog.fetch_next_track(ctx.author.voice.channel.id)
    if next_track_info:
        track_id, title, author, link = next_track_info
        track = await wavelink.YouTubeTrack.search(link)
        if track[0]:
            await vc.play(track[0])
            db_cog.remove_played_track(track_id)  # Remove the track being played from the queue
            print(f"Playing {title} by {author}")
            await ctx.respond(f"Playing {title} by {author}")
        else:
            await ctx.respond("Error playing track")
    else:
        await ctx.respond("End of queue. Use /play to add a song to the queue.")



@bot.slash_command(name="play")
async def play(ctx, search: str):
    guild_id = ctx.guild.id
    if guild_id not in players:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        players[guild_id] = vc  # Store the player instance in the dictionary
    else:
        vc = players[guild_id]

    if ctx.author.voice.channel.id != vc.channel.id:
        return await ctx.respond("You must be in the same voice channel as the bot.")

    tracks = await wavelink.YouTubeTrack.search(search)
    if not tracks:
        await ctx.send(f'No tracks found with query: `{search}`')
        return

    track = tracks[0]
    track_id = db_cog.add_to_queue(ctx.channel.id, track.title, track.author, track.uri, ctx.author.id)
    current_tracks.setdefault(guild_id, []).append(track_id)

    # If nothing is currently playing, play the next track in the queue
    if not vc.is_playing():
        next_track_info = db_cog.fetch_next_track(ctx.channel.id)
        if next_track_info:
            track_id, title, author, link = next_track_info
            if guild_id not in current_tracks:
                current_tracks[guild_id] = []
            current_tracks[guild_id].append(track_id)
            track = await wavelink.YouTubeTrack.search(link)
            if track[0]:
                await vc.play(track[0])
                await ctx.respond(f"Playing {title} by {author}")
    else:
        await ctx.respond(f"Added {track.title} by {track.author} to the queue.")


if __name__ == '__main__':
    bot.load_extension("cogs.ssa")

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
