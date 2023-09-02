import os

import requests
import nextcord as discord
from nextcord.ext import commands
from nextcord import Interaction

CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')


def get_spotify_token():
    auth_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.post(auth_url, {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })

    json_response = auth_response.json()
    return json_response['access_token']


class spotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="playlist", description="Fetches playlist details from Spotify",
                           guild_ids=[int(guild_id) for guild_id in os.getenv("GUILD_ID").split(",")])
    async def _playlist(self, ctx: discord.Interaction, playlist_id: str):
        token = get_spotify_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }
        playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
        playlist_response = requests.get(playlist_url, headers=headers)

        if playlist_response.status_code == 200:
            playlist_data = playlist_response.json()
            playlist_name = playlist_data["name"]
            playlist_description = playlist_data["description"]
            playlist_link = playlist_data["external_urls"]["spotify"]

            await ctx.send(content=f"**{playlist_name}**\n{playlist_description}\nListen here: {playlist_link}")
        else:
            await ctx.send(content=f"Failed to fetch playlist. Error: {playlist_response.status_code}")

    @discord.slash_command(name="track", description="Fetches track details from Spotify",
                           guild_ids=[int(guild_id) for guild_id in os.getenv("GUILD_ID").split(",")])
    async def _track(self, ctx: discord.Interaction, track_name: str):
        token = get_spotify_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }

        search_url = "https://api.spotify.com/v1/search"
        search_response = requests.get(search_url, headers=headers,
                                       params={"q": track_name, "type": "track", "limit": 1})

        track_data = search_response.json()["tracks"]["items"][0]
        track_name = track_data["name"]
        track_artist = track_data["artists"][0]["name"]
        track_link = track_data["external_urls"]["spotify"]

        await ctx.send(content=f"**{track_name}** by *{track_artist}*\nListen here: {track_link}")


def setup(bot):
    bot.add_cog(spotify(bot))
    print("Loaded Spotify")
