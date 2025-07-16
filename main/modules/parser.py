import asyncio
from main.modules.schedule import update_schedule
from main.modules.utils import status_text
from main.modules.db import get_animesdb, get_uploads, save_animedb
from main import app, queue  # ✅ only import app, not status
from main.inline import button1
from config import STATUS_ID, UPLOADS_ID
import feedparser

def trim_title(title: str):
    title, ext = title.replace("[SubsPlease]", "").strip().split("[", maxsplit=2)
    _, ext = ext.split("]", maxsplit=2)
    title = title.strip() + ext
    return title

def parse():
    a = feedparser.parse("https://subsplease.org/rss/")
    b = a["entries"]
    data = []

    for i in b:
        item = {}
        item['title'] = trim_title(i['title'])
        item['size'] = i['subsplease_size']
        item['link'] = i['link']
        data.append(item)

    data.reverse()
    return data

async def auto_parser():
    while True:
        try:
            status = await app.get_messages(UPLOADS_ID, STATUS_ID)  # ✅ fetch status safely
            await status.edit(await status_text("Parsing Rss, Fetching Magnet Links..."), reply_markup=button1)
        except Exception as e:
            print("[WARN] Failed to update status:", e)

        rss = parse()
        data = await get_animesdb()
        uploaded = await get_uploads()

        saved_anime = [i["name"] for i in data]
        uanimes = [i["name"] for i in uploaded]

        for i in rss:
            if i["title"] not in uanimes and i["title"] not in saved_anime:
                if ".mkv" in i["title"] or ".mp4" in i["title"]:
                    await save_animedb(i["title"], i)

        data = await get_animesdb()
        for i in data:
            if i["data"] not in queue:
                queue.append(i["data"])
                print("Saved", i["name"])

        try:
            status = await app.get_messages(UPLOADS_ID, STATUS_ID)  # ✅ fetch again before editing
            await status.edit(await status_text("Idle..."), reply_markup=button1)
            await update_schedule()
        except Exception as e:
            print("[WARN] Failed to update status/schedule:", e)

        await asyncio.sleep(600)
