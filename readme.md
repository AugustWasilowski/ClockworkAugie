ClockworkAugie: A Discord Music Bot
Overview
ClockworkAugie is a versatile Discord music bot designed to enhance your music listening experience on Discord servers. With features ranging from playing tracks to saving your favorite tracks, ClockworkAugie offers a comprehensive music experience.

Features
Play Music: Play music from YouTube directly into your Discord voice channels.
Queue Management: Queue up tracks and manage them with ease.
Favorites: Save your favorite tracks for easy access later.
Advanced Search: Get the top critically acclaimed tracks of an artist with a simple command.
Database Integration: Uses SQLite for storing track data, queues, and user favorites.
Setup & Installation
Clone the repository to your local machine.
Install the required dependencies using pip install -r requirements.txt.
Make sure you have OpenJDK installed for Wavelink.
Set up your environment variables including your Discord token and OpenAI API key.
Run the bot using python main.py.
Usage
Here are some of the primary commands you can use with ClockworkAugie:

/play <URL/track name>: Play a specific track or YouTube link.
/skip: Skip the current track.
/showqueue: Display the current queue of tracks.
/favorite: Save the currently playing track as a favorite.
/playfavorites: Play tracks from your favorites.
/toptracks <artist>: Get the top tracks of a specific artist.
... and many more. Use /help on Discord to see a full list of commands.