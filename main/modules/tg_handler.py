import asyncio
import sys
import os
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import filters
from pyrogram.errors import FloodWait

from main.modules.compressor import compress_video
from main.modules.utils import episode_linker, get_duration, get_epnum, status_text
from main.modules.uploader import upload_video
from main.modules.db import del_anime, get_channel, save_channel, save_uploads, is_voted, save_vote
from main.modules.downloader import downloader
from main.modules.anilist import get_anilist_data, get_anime_img, get_anime_name
from config import INDEX_USERNAME, UPLOADS_USERNAME, UPLOADS_ID, INDEX_ID, STATUS_ID
from main import app, queue
from main.inline import button1


async def tg_handler():
    while True:
        try:
            if len(queue) != 0:
                i = queue[0]
                queue.remove(i)
                val, id, name, ep_num, video = await start_uploading(i)

                await del_anime(i["title"])
                await save_uploads(i["title"])

                status = await app.get_messages(UPLOADS_ID, STATUS_ID)
                await status.edit(await status_text(f"Adding Links To Index Channel ({INDEX_USERNAME})..."), reply_markup=button1)

                await channel_handler(val, id, name, ep_num, video)

                status = await app.get_messages(UPLOADS_ID, STATUS_ID)
                await status.edit(await status_text("Sleeping For 5 Minutes..."), reply_markup=button1)
                await asyncio.sleep(300)
            else:
                status = await app.get_messages(UPLOADS_ID, STATUS_ID)
                if "Idle..." in status.text:
                    try:
                        await status.edit(await status_text("Idle..."), reply_markup=button1)
                    except:
                        pass
                await asyncio.sleep(600)

        except FloodWait as e:
            flood_time = int(e.x) + 5
            status = await app.get_messages(UPLOADS_ID, STATUS_ID)
            try:
                await status.edit(await status_text(f"Floodwait... Sleeping For {flood_time} Seconds"), reply_markup=button1)
            except:
                pass
            await asyncio.sleep(flood_time)
        except:
            pass


async def start_uploading(data):
    try:
        title = data["title"]
        link = data["link"]
        size = data["size"]

        name, ext = title.split(".")
        name += f" [@{UPLOADS_USERNAME}]." + ext
        fpath = "downloads/" + name
        name = name.replace(f" [@{UPLOADS_USERNAME}].", "").replace(ext, "").strip()

        id, img, tit = await get_anime_img(get_anime_name(title))
        msg = await app.send_photo(UPLOADS_ID, photo=img, caption=title)

        print("Downloading -->", name)
        status = await app.get_messages(UPLOADS_ID, STATUS_ID)
        await status.edit(await status_text(f"Downloading {name}"), reply_markup=button1)

        file = await downloader(msg, link, size, title)
        await msg.edit(f"Download Complete : {name}")

        print("Encoding -->", name)
        status = await app.get_messages(UPLOADS_ID, STATUS_ID)
        await status.edit(await status_text(f"Encoding {name}"), reply_markup=button1)

        duration = get_duration(file)
        os.rename(file, "video.mkv")
        compressed = await compress_video(duration, msg, name)

        if compressed == "None" or compressed is None:
            print("Encoding Failed Uploading The Original File")
            os.rename("video.mkv", fpath)
        else:
            os.rename("out.mkv", fpath)

        print("Uploading -->", name)
        status = await app.get_messages(UPLOADS_ID, STATUS_ID)
        await status.edit(await status_text(f"Uploading {name}"), reply_markup=button1)

        message_id = int(msg.message_id) + 1
        video = await upload_video(msg, fpath, id, tit, name, size)

        try:
            os.remove("video.mkv")
            os.remove("out.mkv")
            os.remove(file)
            os.remove(fpath)
        except:
            pass

    except FloodWait as e:
        flood_time = int(e.x) + 5
        status = await app.get_messages(UPLOADS_ID, STATUS_ID)
        try:
            await status.edit(await status_text(f"Floodwait... Sleeping For {flood_time} Seconds"), reply_markup=button1)
        except:
            pass
        await asyncio.sleep(flood_time)

    return message_id, id, tit, name, video


VOTE_MARKUP = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="👍", callback_data="vote1"),
            InlineKeyboardButton(text="♥️", callback_data="vote2"),
            InlineKeyboardButton(text="👎", callback_data="vote3")
        ]
    ]
)

EPITEXT = """
🔰 **Episodes :**

{}
"""


async def channel_handler(msg_id, id, name, ep_num, video):
    try:
        anilist = await get_channel(id)

        if anilist == 0:
            img, caption = await get_anilist_data(name)
            main = await app.send_photo(INDEX_ID, photo=img, caption=caption, reply_markup=VOTE_MARKUP)

            link = f"[{ep_num}](https://t.me/{UPLOADS_USERNAME}/{video})"
            dl = await app.send_message(
                INDEX_ID,
                EPITEXT.format(link),
                disable_web_page_preview=True
            )

            await app.send_sticker(INDEX_ID, "CAACAgUAAx0CXbNEVgABATemYrg6dYZGimb4zx9Q1DAAARzJ_M_NAAI6BQAC7s_BVQFFcU052MmMHgQ")
            dl_id = dl.message_id
            caption += f"\n📥 **Download -** [{name}](https://t.me/{INDEX_USERNAME}/{dl_id})"
            await main.edit_caption(caption, reply_markup=VOTE_MARKUP)

            await save_channel(id, dl_id)
        else:
            dl_id = anilist
            dl_msg = await app.get_messages(INDEX_ID, dl_id)
            text = dl_msg.text
            text += f"\n{ep_num}"

            ent = episode_linker(dl_msg.text, dl_msg.entities, ep_num, f"https://t.me/{UPLOADS_USERNAME}/{video}")
            await app.edit_message_text(INDEX_ID, dl_id, text, entities=ent, disable_web_page_preview=True)

        main_id = dl_id
        info_id = main_id - 1
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="Info", url=f"https://t.me/{INDEX_USERNAME}/{info_id}"),
                InlineKeyboardButton(text="Comments", url=f"https://t.me/{INDEX_USERNAME}/{main_id}?thread={main_id}")
            ]
        ])
        await app.edit_message_reply_markup(UPLOADS_ID, video, reply_markup=buttons)

    except FloodWait as e:
        flood_time = int(e.x) + 5
        status = await app.get_messages(UPLOADS_ID, STATUS_ID)
        try:
            await status.edit(await status_text(f"Floodwait... Sleeping For {flood_time} Seconds"), reply_markup=button1)
        except:
            pass
        await asyncio.sleep(flood_time)


def get_vote_buttons(a, b, c):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text=f"👍 {a}", callback_data="vote1"),
                InlineKeyboardButton(text=f"♥️ {b}", callback_data="vote2"),
                InlineKeyboardButton(text=f"👎 {c}", callback_data="vote3")
            ]
        ]
    )


@app.on_callback_query(filters.regex("vote"))
async def votes_(_, query: CallbackQuery):
    try:
        id = query.message.message_id
        user = query.from_user.id
        vote = int(query.data.replace("vote", "").strip())

        is_vote = await is_voted(id, user)
        if is_vote == 1:
            return await query.answer("You Have Already Voted... You Can't Vote Again")
        await query.answer()

        x = query.message.reply_markup['inline_keyboard'][0]
        a = x[0]['text'].replace('👍', '').strip()
        b = x[1]['text'].replace('♥️', '').strip()
        c = x[2]['text'].replace('👎', '').strip()

        a = int(a or 0)
        b = int(b or 0)
        c = int(c or 0)

        if vote == 1:
            a += 1
        elif vote == 2:
            b += 1
        elif vote == 3:
            c += 1

        buttons = get_vote_buttons(a, b, c)
        await query.message.edit_reply_markup(reply_markup=buttons)
        await save_vote(id, user)

    except FloodWait as e:
        flood_time = int(e.x) + 5
        status = await app.get_messages(UPLOADS_ID, STATUS_ID)
        try:
            await status.edit(await status_text(f"Floodwait... Sleeping For {flood_time} Seconds"), reply_markup=button1)
        except:
            pass
        await asyncio.sleep(flood_time)

    return
