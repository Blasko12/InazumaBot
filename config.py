import os

from dotenv import load_dotenv


load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
RSS_URL = os.getenv("RSS_URL")

canales = os.getenv("DISCORD_CHANNEL_IDS", "")

DISCORD_CHANNEL_IDS = [
    int(canal.strip())
    for canal in canales.split(",")
    if canal.strip().isdigit()
]