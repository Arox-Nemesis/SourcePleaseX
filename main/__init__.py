import time
import os

# 🔧 Delay for time sync (must be before Pyrogram starts)
print("⏳ Waiting 10 seconds to sync time...")
time.sleep(10)

# Optional: Force UTC timezone
os.environ['TZ'] = 'UTC'
try:
    time.tzset()
except:
    pass

from pyrogram import Client
from config import *
import libtorrent as lt

# ✅ Initialize Client
app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ✅ Start Pyrogram after time is stable
app.start()

print("[INFO]: STARTING Lib Torrent CLIENT")
ses = lt.session()
ses.listen_on(6881, 6891)

queue = []

# ✅ Telegram API call happens only after time + client is ready
status = app.get_messages(UPLOADS_ID, STATUS_ID)
