from asyncio import sleep
from datetime import timedelta
from time import time
import os

from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

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
db_last = mongoClient[db_name]["Last"]

AllBots = {}
Status = {"UserName": 0, "ID": 0, "Flood": 0, "Last": 1}
bot = {"username": None, "status": False}


async def main():
    await get_all_bots()
    while True:
        async for msg in client.iter_history(chat, reverse=True, offset_id=Status["Last"]):
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
                except FloodWait as e:
                    wait = e.x + 10 * 60
                    Status["Flood"] = int(time()) + wait
                    await sleep(wait)
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
                    Status["UserName"] += 1
                    await sleep(username_time)
                else:
                    Status["ID"] += 1
                break
        else:
            text += f"\n{line}"
    if edit:
        await msg.edit_text(text, reply_markup=msg.reply_markup)
    await db_last.update_one({}, {"$set": {"last": msg.message_id}}, upsert=True)


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


@client.on_message(filters.command("all", prefixes=".") & filters.outgoing)
async def all_bots(_, msg: Message):
    file = "All-Bots.txt"
    with open(file, "w") as f:
        for i in AllBots.values():
            f.write(f"@{i['username']}\n{i['id']}\n\n")
    await msg.reply_document(file)


@client.on_message(filters.command("status", prefixes=".") & filters.outgoing)
async def bot_status(_, msg: Message):
    if time() > Status["Flood"]:
        flood = "None"
    else:
        flood = str(timedelta(seconds=int(Status["Flood"] - time())))
    text = (f"Last-Message-ID: {Status['Last']}\n\n"
            f"By-UserName: {Status['UserName']}\n\n"
            f"By-ID: {Status['ID']}\n\n"
            f"Flood: {flood}")
    await msg.edit_text(text)


async def get_all_bots():
    async for b in db.find({}):
        AllBots[b["username"]] = b
    last = await db_last.find_one({})
    if last is None:
        Status["Last"] = 1
        await db_last.insert_one({"last": 1})
    else:
        Status["Last"] = last["last"]


client.start()
client.loop.run_until_complete(main())
