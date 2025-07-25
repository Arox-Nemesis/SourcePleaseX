import time
import os
import asyncio
from uvloop import install
from contextlib import closing, suppress

# 🕒 Time sync fix before Telegram connection
print("⏳ Waiting 30 seconds to sync time with Telegram...")
time.sleep(30)
os.environ['TZ'] = 'UTC'
try:
    import time as tm
    tm.tzset()
except:
    pass

# Safe to import after time sync
from main.modules.parser import auto_parser
from main.modules.schedule import update_schedule
from main import app
from pyrogram import filters, idle
from pyrogram.types import Message
from main.modules.tg_handler import tg_handler

loop = asyncio.get_event_loop()

@app.on_message(filters.command(["start", "help", "ping"]))
async def start(bot, message: Message):
    return await message.reply_text(
        "[⭐️](https://te.legra.ph/file/9a365462d71dbb0042c6e.jpg) **Bot Is Online...**\n\n"
        "**Updates :** @sourcepleaseindex **| Support :** @thoursbridi"
    )

async def start_bot():
    print("==================================")
    print("[INFO]: Starting Pyrogram Bot Client")
    await app.start()

    from config import UPLOADS_ID, STATUS_ID
    import main
    main.status = await app.get_messages(UPLOADS_ID, STATUS_ID)

    print("[INFO]: AutoAnimeBot Started Bot Successfully")
    print("==========JOIN @sourcepleaseindex==========")

    print("[INFO]: Updating schedule message")
    await update_schedule()

    print("[INFO]: Adding Parsing Task")
    asyncio.create_task(auto_parser())
    asyncio.create_task(tg_handler())

    await idle()

    print("[INFO]: BOT STOPPED")
    await app.stop()

    for task in asyncio.all_tasks():
        task.cancel()

if __name__ == "__main__":
    install()
    with closing(loop):
        with suppress(asyncio.exceptions.CancelledError):
            loop.run_until_complete(start_bot())
            loop.run_until_complete(asyncio.sleep(3.0)) 
