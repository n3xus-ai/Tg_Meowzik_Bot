from __future__ import unicode_literals 
import os, asyncio, json, requests
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from config import owner_id, bot_token, sudo_chat_id
from youtube_search import YoutubeSearch

#Initialize--------------------------
app = Client(
    ":memory:",
    bot_token=bot_token,
    api_id=1667849,
    api_hash="b719710209932bff18219f4064e92388",
)

queue=[]
playing=False
current_player=None

# Os Determination-------------------

if os.name == "nt":
    kill = "tskill"
else:
    kill = "killall -9"

# Get User Input---------------------
def kwairi(message):
    query = ""
    for i in message.command[1:]:
        query += f"{i} "
    return query

def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)

def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(':'))))
    
def listy(queue):
    liste=""
    for i,qq in enumerate(queue):
        if i==0:
            continue
        liste = liste+ f"{i}.**Song:**`{qq[3]}` Via {qq[5]}- Requested by {qq[2]}\n"
    return liste

async def getadmins(chat_id):
    admins = []
    async for i in app.iter_chat_members(chat_id, filter="administrators"):
        admins.append(i.user.id)
    admins.append(owner_id)
    return admins

#Help  ------------------------------------------------------------------------------------
@app.on_message(
    filters.command(["help"]) & filters.chat(sudo_chat_id) & ~filters.edited
)
async def help(_, message: Message):
    await message.reply_text(
        """**Currently These Commands Are Supported.**
/help To Show This Message.
/skip To Skip Any Playing Music.
/queue To See Queue List.
/saavn "Song_Name" To Play A Song From Jiosaavn.
/playlist "saavn_playlist_link" To add all songs to Queue and Play.
/youtube "Song_Name" To Search For A Song And Play The Top-Most Song Or Play With A Link.
/deezer "Song_Name" To Play A Song From Deezer.
/telegram While Tagging a Song To Play From Telegram File.

**Admin Commands**:
/kill Yeah it kills the bot LOL
/clearqueue It clears entire Queue in a snap"""
    )

#Repo  ------------------------------------------------------------------------------------
@app.on_message(
    filters.command(["repo"]) & filters.chat(sudo_chat_id) & ~filters.edited
)
async def repo(_, message: Message):
    m= await message.reply_text(text="""[Meowzik Repo](https://github.com/Devanagaraj/Tg_Meowzik_Bot) | [Support Group](https://t.me/TGVCSUPPORT)""", disable_web_page_preview=True)
    await asyncio.sleep(10)
    await m.delete()
    await message.delete()

#PLAY-------------------------------------------------------------------------------------------------------------
async def play():
    global queue
    global playing
    global mm
    global s
    while len(queue)>0:
        mm = await app.send_photo(sudo_chat_id,photo=f"{queue[0][6]}",
            caption=f"Now Playing `{queue[0][3]}`  by `{queue[0][4]}` Via {queue[0][5]}\nRequested by {queue[0][2]}",
            reply_markup=InlineKeyboardMarkup( [[ 
            InlineKeyboardButton(f"Skip", callback_data="skip_"), 
            InlineKeyboardButton(f"Queue", callback_data="queue_")
            ]] ))
        if queue[0][5]=="Telegram":
            await app.download_media(queue[0][0], file_name="audio.webm")
            queue[0][0]= "downloads/audio.webm --no-video"
        s = await asyncio.create_subprocess_shell(
        f"mpv {queue[0][0]} --profile=low-latency --no-video",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,)
        await s.wait()
        await mm.delete()
        try:
            os.system(f"{kill} mpv")
        except:
            pass
        if len(queue)<=1:
            playing=False
        del queue[0]
#SKIP---------------------------------------------------------------------------------------------------------------
@app.on_message(filters.command(["skip"]) & filters.chat(sudo_chat_id) & ~filters.edited)
async def skip(_, message: Message):
    global queue
    global mm
    global s
    list_of_admins = await getadmins(message.chat.id)
    list_of_admins.append(queue[0][7])
    if message.from_user.id not in list_of_admins:
        a= await app.send_message(sudo_chat_id,text=f"Skipping songs without admin permission is Sin! \n Want a Good Ban {message.from_user.mention}?")
        await asyncio.sleep(5)
        await a.delete()
        await message.delete()
        return
    if len(queue)<=1:
        m= await message.reply_text("Can't skip an empty queue!")
        await asyncio.sleep(5)
        await m.delete()
        await message.delete()
        return
    await mm.delete()
    try:
        os.system(f"{kill} mpv")
    except:
        pass
    m= await message.reply_text("Skipped!")
    await asyncio.sleep(5)
    await m.delete()
    await message.delete()
    
@app.on_callback_query(filters.regex("skip_"))
async def callback_query_skip(_, message: Message):
    global queue
    global mm
    list_of_admins = await getadmins(sudo_chat_id)
    if message.from_user.id not in list_of_admins:
        a= await app.send_message(sudo_chat_id,text=f"Skipping songs without admin permission is Sin! \n Want a Good Ban {message.from_user.mention}?")
        await asyncio.sleep(5)
        await a.delete()
        return
    elif len(queue)<=1:
        m= await app.send_message(sudo_chat_id,text="Can't skip an empty queue!")
        await asyncio.sleep(5)
        await m.delete()
        return
    await mm.delete()
    try:
        os.system(f"{kill} mpv")
    except:
        pass
    m= await app.send_message(sudo_chat_id,text="Skipped!")
    await asyncio.sleep(5)
    await m.delete()
 
#QUEUE-----------------------------------------------------------------------------------------------------------

@app.on_message(filters.command(["queue"]) & filters.chat(sudo_chat_id) & ~filters.edited)
async def q(_, message: Message):
    global queue
    if len(queue)<=1:
        q= await message.reply_text("Queue is empty!")
        await asyncio.sleep(5)
        await q.delete()
        await message.delete()
        return
    liste= listy(queue)
    if len(liste) > 4096:
        filename = "Queue.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(liste)
        q= await message.reply_document(
            document=filename,
            caption="Queue List",
            disable_notification=True,
        )
        os.remove(filename)
        await asyncio.sleep(10)
        await q.delete()
        await message.delete
    else:
        q= await message.reply_text(liste)
        await asyncio.sleep(10)
        await q.delete()
        await message.delete
    
@app.on_callback_query(filters.regex("queue_"))
async def callback_query_queue(_, message):
    global queue
    if len(queue)<=1:
        q= await app.send_message(sudo_chat_id,text= f"Queue is empty! \nClicked by {message.from_user.mention}")
        await asyncio.sleep(5)
        await q.delete()
        return
    liste= listy(queue)
    if len(liste) > 4096:
        filename = "Queue.txt"
        with open(filename, "w+", encoding="utf8") as out_file:
            out_file.write(liste)
        q= await app.send_document(sudo_chat_id,
            document=filename,
            caption=f"Queue List \n Clicked by {message.from_user.mention}",
            disable_notification=True,
        )
        os.remove(filename)
        await asyncio.sleep(10)
        await q.delete()
    else:
        q= await app.send_message(sudo_chat_id,text= f"{liste} \nClicked by {message.from_user.mention}")
        await asyncio.sleep(10)
        await q.delete()
    
#CLEAR QUEUE----------------------------------------------------------------------------------------------------------------------

@app.on_message(filters.user(owner_id) & filters.command(["clearqueue"]) & filters.chat(sudo_chat_id) & ~filters.edited)
async def q(_, message: Message):
       global queue
       global playing
       global mm
       queue=[]
       q= await message.reply_text("Queue cleared successfully")
       await asyncio.sleep(3)
       await q.delete()
       await mm.delete()
       try:
        os.system(f"{kill} mpv")
       except:
        pass
       playing=False
       await message.delete()
       
# Deezer----------------------------------------------------------------------------------------

@app.on_message(
    filters.command(["deezer"])
    & filters.chat(sudo_chat_id)
    & ~filters.edited
)
async def deezer(_, message: Message):
    global blacks
    global playing
    global queue
    global m
    query = kwairi(message)
    if not message.from_user.id:
        return
    current_player = message.from_user.id
    m = await message.reply_text(f"Searching for `{query}`on Deezer")
    try:
        resp= requests.get(f"https://thearq.tech/deezer?query={query}&count=1").text
        r = json.loads(resp)
        sname = r[0]["title"]
        sduration = (r[0]["duration"])
        thumbnail = r[0]["thumbnail"]
        singers = r[0]["artist"]
        slink = r[0]["url"]
        module="Deezer"
    except:
        await m.edit("Aww...got some error! Try Again")
        await asyncio.sleep(5)
        await m.delete()
        await message.delete()
        return
    await m.delete()
    await message.delete()
    q= [slink,sduration,message.from_user.first_name,sname,singers,module,thumbnail,current_player]
    queue.append(q)
    if playing:
        return
    else:
        playing=True
        await play()

# Youtube---------------------------------------------------------------------------------------
@app.on_message(filters.command(["youtube"]) & filters.chat(sudo_chat_id) & ~filters.edited)
async def yt(_, message: Message):
    global blacks
    global playing
    global queue
    global m
    query = kwairi(message)
    if not message.from_user.id:
        return
    current_player = message.from_user.id
    m = await message.reply_text(f"Searching for `{query}`on YouTube")
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        slink= f"https://youtube.com{results[0]['url_suffix']}"
        title = results[0]["title"]
        singers = results[0]["channel"]
        thumbnail = results[0]["thumbnails"][0]
        sduration = results[0]["duration"]
        duration= time_to_seconds(sduration)
        views = results[0]["views"]
        module = "YouTube"
        if int(duration)>=1800: #duration limit
                await m.edit("Bruh! Only songs within 30 Mins")
                return    
    except Exception as e:
        await m.edit("can't find anything!")
        await asyncio.sleep(3)
        await m.delete()
        await message.delete()
        print(str(e))
        return
    await m.delete()
    await message.delete()
    q= [slink,sduration,message.from_user.first_name,title,singers,module,thumbnail,current_player]
    queue.append(q)
    if playing:
        return
    else:
        playing=True
        await play()
    
# Jiosaavn--------------------------------------------------------------------------------------

@app.on_message(
    filters.command(["saavn"])
    & filters.chat(sudo_chat_id)
    & ~filters.edited
)
async def jiosaavn(_, message: Message):
    global blacks
    global playing
    global queue
    global m
    query = kwairi(message)
    if not message.from_user.id:
        return
    current_player = message.from_user.id
    m = await message.reply_text(f"Searching for `{query}`on JioSaavn")
    try:
        try:
           resp= requests.get(f"https://jiosaavnapi.bhadoo.uk/result/?query={query}").text
           r = json.loads(resp)
        except:
            resp= requests.get(f"https://thearq.tech/saavn?{query}=blah&count=1").text
            r = json.loads(resp)
        sname = r[0]['song']
        slink = r[0]['media_url']
        slink = slink.replace('500x500','200x200')
        singers = r[0]['singers']
        sthumb = r[0]['image']
        sduration = convert_seconds(int(r[0]['duration']))
        module="JioSaavn"
    except Exception as e:
        print(e)
        await m.edit("Aww...got some error! Try Again")
        await asyncio.sleep(5)
        await m.delete()
        return
    await m.delete()
    await message.delete()
    q= [slink,sduration,message.from_user.first_name,sname,singers,module,sthumb,current_player]
    queue.append(q)
    if playing:
        return
    else:
        playing=True
        await play()
        

# Jiosaavn Playlist--------------------------------------------------------------------------------------

@app.on_message(
    filters.command(["playlist"])
    & filters.chat(sudo_chat_id)
    & ~filters.edited
)
async def playlist(_,message: Message):
    global queue
    global playing
    global m
    if not message.from_user.id:
        return
    current_player = message.from_user.id
    list_of_admins = await getadmins(sudo_chat_id)
    if message.from_user.id not in list_of_admins:
        a= await app.send_message(sudo_chat_id,text=f"Why don't you get an AdminTag? to use playlist {message.from_user.mention}...")
        await asyncio.sleep(5)
        await a.delete()
        await message.delete()
        return
    query = kwairi(message)
    m = await message.reply_text("Searching for Playlist and trying to get songs....")
    try:
        resp= requests.get(f"https://thearq.tech/splaylist?query={query}").json()
        for i in resp:
            sname = i['song']
            slink = i['media_url']
            slink = slink.replace('500x500','200x200')
            singers = i['singers']
            sthumb = i['image']
            sduration = convert_seconds(int(i['duration']))
            module="JioSaavn Playlist"
            q= [slink,sduration,message.from_user.first_name,sname,singers,module,sthumb,current_player]
            queue.append(q)
        await m.edit(f"Added {len(resp)} songs from Playlist link")
        await asyncio.sleep(5)
        await m.delete()
    except Exception as e:
        print(e)
        await m.edit("Use Jiosaavn playlist link only! or check logs for other errors")
        await asyncio.sleep(5)
        await m.delete()
        await message.delete()
        return
    await message.delete()
    if playing:
        return
    else:
        playing=True
        await play()

# Telegram--------------------------------------------------------------------------------------

@app.on_message(
    filters.command(["telegram"])
    & filters.chat(sudo_chat_id)
    & ~filters.edited
)
async def telegram(_, message: Message):
    global blacks
    global queue
    global playing
    global m
    query = kwairi(message)
    if not message.from_user.id:
        return
    elif not message.reply_to_message.media:
        await message.reply_text("Reply To A Telegram Audio To Play It.")
        return
    elif message.reply_to_message.audio:
        if int(message.reply_to_message.audio.file_size) >= 104857600:
            await message.reply_text('Bruh! Only songs within 100 MB')
            return
        else:
            slink= message.reply_to_message.audio.file_id
    elif message.reply_to_message.document:
        if int(message.reply_to_message.document.file_size) >= 104857600:
            await message.reply_text('Bruh! Only songs within 100 MB')
            return
        else:
            slink= message.reply_to_message.document.file_id
    current_player = message.from_user.id
    m = await message.reply_text(f"Added `{message.reply_to_message.link}` to playlist")
    module="Telegram"
    sname= ''
    sduration= ''
    sname=''
    singers=''
    sthumb="tg.png"
    await asyncio.sleep(5)
    await m.delete()
    await message.delete()
    q= [slink,sduration,message.from_user.first_name,sname,singers,module,sthumb,current_player]
    queue.append(q)
    if playing:
        return
    else:
        playing=True
        await play()
        
        
#KILL--------------------------------------------------------------
@app.on_message(filters.user(owner_id) & filters.command(["kill"]) & filters.chat(sudo_chat_id) & ~filters.edited)
async def quit(_, message: Message):
    await message.reply_text("aww snap >-< , GoodByeCruelWorld")
    queue=[]
    print("Exiting...........")
    os.system(f"{kill} mpv")
    exit()
   
app.run()
