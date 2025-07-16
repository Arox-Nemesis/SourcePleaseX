from pyrogram import Client
from config import *
import libtorrent as lt

# ✅ Initialize Pyrogram Client
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ✅ Libtorrent session setup (but don't use Telegram yet)
print("[INFO]: LibTorrent Session Initializing")
ses = lt.session()
ses.listen_on(6881, 6891)

# ✅ Initialize your global queue
queue = []

# ❌ DO NOT call app.start() or get_messages() here
# These must be done AFTER app.start() in main.py
