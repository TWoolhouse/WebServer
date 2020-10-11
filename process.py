import debug
# debug.enable()

import re
import os
import json
import time
import datetime
from path import PATH
import pytz
import database as db

CHAT_NAME = "Poppy Tester"
# CHAT_NAME = "Lani Best Girl"
IG_PATH = "C:/dev/Code/Node/Project/Instagram/"

IG_DIR = f"{IG_PATH}chat/{CHAT_NAME}/"
# URL_RE = re.compile("""(http(s)?:\\/\\/)?(www\\.)?(?:[-a-zA-Z0-9@:%_\\+~#=]{2,128}\\.?){1,6}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%_\\+.,~#?&//=]*)""")
URL_RE = re.compile(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?")

def read_all_data():
    dir_msg = IG_DIR+"message/meta/"
    count = 0
    start = time.time()
    for fi, filename in enumerate(os.listdir(dir_msg)):
        mid = time.time()
        with open(dir_msg+filename, encoding="utf-8") as file:
            data = json.load(file)
        yield from data
        end = time.time()
        print(fi, count, round(end - mid, 3), round(end - start, 3))
        count += len(data)
        # break

def read_partial_data():
    dir_msg = IG_DIR+"message/meta/"
    start = time.time()
    mid = start
    for fi, filename in enumerate(os.listdir(dir_msg)):
        end = time.time()
        print(fi, round(end - start, 3), round(end - mid, 3))
        mid = time.time()
        yield dir_msg+filename

def read_partial(filename: str):
    with open(filename, encoding="utf-8") as file:
        data = json.load(file)
    yield from data

def read_all_users():
    dir_usr = IG_DIR+"user/"
    for filename in os.listdir(dir_usr):
        if "meta" in filename:
            continue
        with open(dir_usr+filename, encoding="utf-8") as file:
            data = json.load(file)
        yield data

def read_active_users():
    dir_usr = IG_DIR+"user/meta"
    with open(dir_usr, encoding="utf-8") as file:
        data = json.load(file)
    for u in data["active"]:
        yield u, True
    for u in data["lost"]:
        yield u, False

### DATABASE NAME ###

OUTPUT_FILE = None
database = db.Database(PATH+f"resource/database/{CHAT_NAME.lower().replace(' ', '_')}.test.db")

### DATABASE NAME ###

e_types = {}

def process_likes(element: dict, eid: int):
    tbl = database["Like"]
    usr = database["User"]
    for like in element["likes"]:
        if (u := database().select(usr, db.Condition(like))()[0]):
            database().insert(tbl, eid, u)
        else:
            database().insert(tbl, eid, 1) # Deleted User

def process_text(element, eid, tbl, link=False):
    if link:
        # print(element["text"], file=OUTPUT_FILE, flush=True)
        urls = URL_RE.finditer(element["text"])
        if urls:
            tid = database().insert(tbl, eid, element["text"])
            ltb = e_types["link"][1]
            for url in urls:
                # print(url[0])
                database().insert(ltb, tid, url.group(0), url.start())
            return tid
    else:
        return database().insert(tbl, eid, element["text"])

def process(element: dict) -> int:
    # Text
    if element["type"] in ("text", "link", "like"):
        if element["type"] == "like":
            element["text"] = U"2764"
        tid, tbl = e_types["text"]
        eid = yield tid
        process_text(element, eid, tbl, link=True)

    # Action
    elif element["type"] in ("action", "call"):
        tid, tbl = e_types["action"]
        eid = yield tid
        if element["type"] == "call":
            action = "c"
            desc = "s" if element["call"] == "start" else "e"
        else:
            alookup = {"rename": "n", "added": "a", "remove": "r"}
            action = alookup[element["action"]]
            desc = element["desc"]
        database().insert(tbl, eid, action, desc)

    # Placeholder
    elif element["type"] in ("placeholder", "story"):
        tid, tbl = e_types["placeholder"]
        eid = yield tid
        if element["type"] == "story":
            ptype = "s"
            msg = False
        else:
            if "title" not in element:
                element["title"] = "u"
            plookup = {"Photo Unavailable": "i", "Video Unavailable": "v", "Post Unavailable": "p", "u": "u"}
            ptype = plookup[element["title"]]
            msg = element["msg"]

        if msg:
            database().insert(tbl, eid, ptype, msg)
        else:
            database().insert(tbl, eid, ptype)

    # Media
    elif element["type"] in ("media", "image", "video", "audio", "gif"):
        tid, tbl = e_types["media"]
        eid = yield tid
        if element["type"] == "media":
            element["type"] = element["mtype"]

        database().insert(tbl, eid, element["type"][0].lower()) 

    # Share
    elif element["type"] in ("share", "profile", "live", "tv"):
        tid, tbl = e_types["share"]
        eid = yield tid

        if element["type"] == "profile":
            element["author"] = element["profile"]
            stype = "u"
        
        elif element["type"] == "live":
            element["code"] = False
            stype = "l"

        elif element["type"] == "tv":
            stype = "t"
            element["text"] = element["title"]

        else:
            stype = "p"
            if "code" not in element:
                element["code"] = False

        user = database().select(database["User"], db.Condition(element["author"]))()
        if not user:
            author = 1 # DELETED
        else:
            author = user[0]

        if element["type"] == "profile":
            element["code"] = False

        if "text" not in element:
            element["text"] = False

        # if element["text"]:
        #     element["text"] = process_text(element, eid, e_types["text"][1])

        cols = {}
        for c, v in (("code", element["code"]), ("type", stype), ("text", element["text"])):
            if v:
                cols[c] = v

        database().insert(tbl, eid, author, cols=cols)

        # Foreign("author", tbl_usr
        # "code", db.Type.String
        # "type", db.Type.Char
        # Foreign("text", tbl_txt

    # Other
    else:
        raise TypeError(element)

def generate_database():
    database.new()
    with database:
        tbl_usr = database.table("User", db.Column("uid", db.tp.INT, db.tp.NULL), db.Column("username", db.tp.STR, db.tp.NULL), db.Column("text", db.tp.STR))
        tbl_usr_act = database.table("User Active", db.Column.Foreign("uid", tbl_usr), db.Column("active", db.tp.TINY))
        tbl_etp = database.table("Element Type", db.Column("name", db.tp.STR, db.tp.NULL))
        tbl_elm = database.table("Element", db.Column("mid", db.tp.STR, db.tp.NULL), db.Column("time", db.tp.DATETIME, db.tp.NULL), db.Column.Foreign("eti", tbl_etp), db.Column.Foreign("user", tbl_usr))

        print("Users")
        with database("Users") as dbi:
            dbi.insert(tbl_usr, 0, "DELETED", "DELETED USER")
            for user in read_all_users():
                dbi.insert(tbl_usr, user["id"], user["username"], user["text_name"])
            for user, active in read_active_users():
                dbi.insert(tbl_usr_act, dbi.select(tbl_usr, db.Condition(user))()[0], 1 if active else 0)

        print("Element Types")
        tbl_lik = database.table("Like", db.Column.Foreign("eid", tbl_elm), db.Column.Foreign("uid", tbl_usr))
        tbl_txt = database.table("Text", db.Column.Foreign("eid", tbl_elm), db.Column("text", db.tp.STR))
        e_type_col = {
            # MUST BE THIS ORDER
            "text": None,
            "action": [db.Column.Foreign("eid", tbl_elm), db.Column("action", db.tp.CHR), db.Column("desc", db.tp.STR)],
            "placeholder": [db.Column.Foreign("eid", tbl_elm), db.Column("type", db.tp.CHR), db.Column("msg", db.tp.STR)],
            "media": [db.Column.Foreign("eid", tbl_elm), db.Column("type", db.tp.CHR)],
            "share": [db.Column.Foreign("eid", tbl_elm), db.Column.Foreign("author", tbl_usr), db.Column("code", db.tp.STR), db.Column("type", db.tp.CHR), db.Column("text", db.tp.STR)],
            "link": [db.Column.Foreign("text", tbl_txt), db.Column("url", db.tp.STR), db.Column("pos", db.tp.INT)],
            # "story": [0, db.Column()], # Turn into Placeholder
            # "live": [db.Column.Foreign("author", tbl_usr)], # Merge with Share
            # "tv": [db.Column.Foreign("author", tbl_usr), db.Column("code", db.Type.String), db.Column("text", db.Type.String)], # Merge with Share
            # "call": [db.Column("type", db.Type.TinyInt)], # Merge with action
        }
        for etype, value in e_type_col.items():
            et = e_types[etype] = [0, None]
            et[0] = database().insert(tbl_etp, f"ElmType{etype.title()}" if value is not None else "Text")
            if value is not None:
                et[1] = database.table(f"ElmType{etype.title()}", *value)
            else:
                et[1] = tbl_txt

    for filename in read_partial_data():
        with database:
            with database() as dbi:
                for element in read_partial(filename):
                    user = dbi.select(tbl_usr, db.Condition(element["user"]))()[0]
                    dt = datetime.datetime.fromtimestamp(element["time"] / 1000000, datetime.timezone.utc).astimezone(pytz.timezone("Europe/London"))

                    proc = process(element)
                    eid = dbi.insert(tbl_elm, element["id"], dt, proc.send(None), user)
                    try:
                        proc.send(eid)
                    except StopIteration:    pass
                    except Exception:
                        print(element)
                        raise
                    if "likes" in element:
                        process_likes(element, eid)

### END OF PROCESSING ###

with open("output.out", "w", encoding="utf-8") as OUTPUT_FILE:
    generate_database()

