import os, asyncio
import yt_dlp
from pyrogram import Client, filters
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

# --- FIXED: Ab direct number bhi daal sakta hai, Env bhi chalega ---
API_ID = int(os.getenv("API_ID", "37146575")) # Yahan apna ID daal de ya Railway Variable bana de
API_HASH = os.getenv("API_HASH", "4617e8b7d1040d7d895ec39de8eae4e5")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8252566284:AAH84AVugAXHYgvrJvPqI7-6QfC3GCwLYZ8")
SESSION_STRING = os.getenv("SESSION_STRING", "BQI2z88ASotzhCfCbI024XcDPNqOuzV7a7mkxUeqEPOhV_-J1zQMsCFem1M2DlT5rdvDi5E-GyXmvlL8jiKqvZPyLKTqIbceF7PXctsaW4T6zSnwIhPML5-q9x8x_E5u6uH8JfhJIPWpH0J29QzQt1gxn3oVvatVcwjh0lveIFwjkMu2hoFC0LGwoSEF6Jyw7k8OLQhBSGciwSBesvCvze0aw6Ls_-3XErM1GbQlJtkShPavbG_gN_MQ3Fo00VGLfI9qWyGetrH6TpbtXL3Z_PsYaSj1yBkA6pbKrBZcCu28UZNRdcaQqG0PDDVYqQCp_GDo87Va5SOqLGqfK8WvxTIQXcBnZgAAAAH3BaEwAA")
# --------------------------------------------------------------------

app = Client("MusicBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_app = Client("UserBot", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)
call_py = PyTgCalls(user_app)

queues = {}
WATERMARK = "\n\n@epic_india"

def get_url(query):
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True, 'noplaylist': True, 'default_search': 'ytsearch1'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info: info = info['entries'][0]
        return info['url'], info['title']

@call_py.on_update()
async def stream_end_handler(_, update):
    try:
        if hasattr(update, 'stream_end') and update.stream_end:
            chat_id = update.chat_id
            if chat_id in queues and queues[chat_id]:
                queues[chat_id].pop(0)
                if queues[chat_id]:
                    nxt = queues[chat_id][0]
                    url, title = await asyncio.to_thread(get_url, nxt['query'])
                    await call_py.play(chat_id, MediaStream(url))
                    await app.send_message(chat_id, f"▶️ **Now Playing:** {title}\n👤 Requested by: {nxt['mention']}{WATERMARK}")
                else:
                    queues.pop(chat_id, None)
    except: pass

@app.on_message(filters.command(["play","vplay","stop","skip","queue"]) & filters.group)
async def handler(_, m):
    mention = m.from_user.mention if m.from_user else "Unknown"
    cmd = m.command[0].lower()

    if cmd == "stop":
        queues.pop(m.chat.id, None)
        try: await call_py.leave(m.chat.id)
        except: pass
        await m.reply(f"⏹ **Stopped & Queue cleared**\nBy: {mention}{WATERMARK}")
        return

    if cmd == "skip":
        if m.chat.id in queues and queues[m.chat.id]:
            old = queues[m.chat.id].pop(0)
            if queues[m.chat.id]:
                nxt = queues[m.chat.id][0]
                url, _ = await asyncio.to_thread(get_url, nxt['query'])
                await call_py.play(m.chat.id, MediaStream(url))
                await m.reply(f"⏭ **Skipped:** {old['title']}\n▶️ **Now:** {nxt['title']}\n👤 Requested by: {nxt['mention']}{WATERMARK}")
            else:
                try: await call_py.leave(m.chat.id)
                except: pass
                await m.reply(f"⏭ Skipped, Queue empty{WATERMARK}")
        return

    if cmd == "queue":
        q = queues.get(m.chat.id, [])
        if not q: await m.reply(f"Queue khali hai{WATERMARK}"); return
        text = "**Queue:**\n"
        for i, d in enumerate(q, 1):
            text += f"{i}. {d['title']} - {d['mention']}\n"
        await m.reply(text + WATERMARK)
        return

    if len(m.command) < 2:
        await m.reply(f"Gaane ka naam de bhai! Ex: `/play kesariya`{WATERMARK}")
        return

    query = m.text.split(None, 1)[1]
    msg = await m.reply(f"🔎 **Searching:** {query}\nBy: {mention}{WATERMARK}")

    try:
        url, title = await asyncio.to_thread(get_url, query)
    except Exception as e:
        await msg.edit(f"Error: {e}{WATERMARK}")
        return

    if m.chat.id not in queues: queues[m.chat.id] = []
    data = {"query": query, "title": title, "mention": mention}

    if not queues[m.chat.id]:
        queues[m.chat.id].append(data)
        try:
            await call_py.play(m.chat.id, MediaStream(url))
            await msg.edit(f"▶️ **Now Playing:** {title}\n👤 **Requested by:** {mention}{WATERMARK}")
        except Exception as e:
            queues[m.chat.id].pop(0)
            await msg.edit(f"❌ Error: {e}{WATERMARK}")
    else:
        queues[m.chat.id].append(data)
        await msg.edit(f"➕ **Added to Queue #{len(queues[m.chat.id])}**\n🎵 {title}\n👤 **Requested by:** {mention}{WATERMARK}")

async def main():
    await user_app.start()
    await app.start()
    await call_py.start()
    print("Bot LIVE - Private + All GC + MediaStream + @epic_india")
    await asyncio.Event().wait()

asyncio.run(main())
