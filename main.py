from asyncio import sleep
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.types import Message


api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
session = os.environ.get("String_Session")
chat = int(os.environ.get("Channel_ID"))
offline_mark = os.environ.get("Offline_Mark")
send_time = int(os.environ.get("Send_Time"))
username_time = int(os.environ.get("UserName_Time"))
time_out = int(os.environ.get("Time_Out"))
sleep_time = int(os.environ.get("Sleep_Time"))
db_link = os.environ.get("DataBase_Link")
db_name = os.environ.get("DataBase_Name")


client = Client(session, api_id, api_hash)

mongoClient = AsyncIOMotorClient(db_link)
db = mongoClient[db_name]["Bots"]

AllBots = {}
bot = {"username": None, "status": False}


async def main():
    await get_all_bots()
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
                    work, by_username = await check_bot(word)
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
                if by_username:
                    await sleep(username_time)
                break
        else:
            text += f"\n{line}"
    if edit:
        await msg.edit_text(text, reply_markup=msg.reply_markup)


async def check_bot(username):
    bot["username"] = username[1:]
    bot["status"] = False
    if username[1:] in AllBots:
        b = AllBots[username[1:]]
        await client.send_message(b["id"], "/start")
        by_username = False
    else:
        msg = await client.send_message(username[1:], "/start")
        data = {"id": msg.chat.id, "username": username[1:]}
        await db.insert_one(data)
        AllBots[username[1:]] = data
        by_username = True
    await sleep(time_out)
    return bot["status"], by_username


@client.on_message(filters.bot)
async def response(_, msg):
    if msg.chat.username == bot["username"]:
        bot["status"] = True


async def get_all_bots():
    async for b in db.find({}):
        AllBots[b["username"]] = b


client.start()
client.loop.run_until_complete(main())
