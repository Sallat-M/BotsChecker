from asyncio import sleep
import os

from pyrogram import Client, filters
from pyrogram.types import Message


api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session = os.environ.get("String_Session")
chat = int(os.environ.get("Channel_ID"))
offline_mark = os.environ.get("Offline_Mark")
send_time = int(os.environ.get("Send_Time"))
time_out = int(os.environ.get("Time_Out"))
sleep_time = int(os.environ.get("Sleep_Time"))


client = Client(session, api_id, api_hash)
bot = {"username": None, "status": False}


async def main():
    while True:
        async for msg in client.iter_history(chat, reverse=True):
            if msg.text:
                try:
                    await check_msg(msg)
                except Exception as e:
                    print(f"Error: {e}")
        await sleep(sleep_time)


async def check_msg(msg: Message):
    text = ""
    edit = False
    for line in msg.text.markdown.split('\n'):
        for word in line.split():
            if word.startswith('@') and word.lower().endswith('bot'):
                off = line.find(offline_mark)
                await sleep(send_time)
                try:
                    work = await check_bot(word)
                except Exception as e:
                    print(f"Error: {e}")
                    continue
                if work:
                    if off > -1:
                        text += f"\n{line[:off - 1]}"
                        edit = True
                    else:
                        text += f"\n{line}"
                else:
                    if off > -1:
                        text += f"\n{line}"
                    else:
                        text += f"\n{line} {offline_mark}"
                        edit = True
                break
        else:
            text += f"\n{line}"
    if edit:
        await msg.edit_text(text, reply_markup=msg.reply_markup)


async def check_bot(username):
    bot["username"] = username[1:]
    bot["status"] = False
    await client.send_message(username, "/start")
    await sleep(time_out)
    return bot["status"]


@client.on_message(filters.bot)
async def response(_, msg):
    if msg.chat.username == bot["username"]:
        bot["status"] = True


client.start()
client.loop.run_until_complete(main())
