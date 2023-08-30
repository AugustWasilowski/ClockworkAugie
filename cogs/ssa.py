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
openai.api_key = os.getenv("OPENAI_API_KEY")


class ssa(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def process_ssa_message(self, interaction, message):
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


def setup(bot):
    bot.add_cog(ssa(bot))
    print("Loaded Second Shift Augie.")
