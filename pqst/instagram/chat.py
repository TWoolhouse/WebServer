import website
import database as db
import datetime
from interface import Interface
from . import dbc
from .element import Element

class Chat(website.Request):

    def init(self, chat: dbc.Chat):
        self.chat = chat.name
        self.eid = self.client.query["elm"]

    async def handle(self):
        self.client.buffer << website.buffer.Python(f"{website.path}page/instagram/chat.html", self)

class BaseMessage(website.Request):

    def init(self, chat: dbc.Chat, dbi, eid: int):
        self.chat = chat
        self.dbi = dbi
        self.eid = eid

    async def handle(self):

        # 0:id, 1:mid, 2:time, 3:eti, 4:user
        elm = (await self.dbi.select(self.dbi["Element"], self.eid))()
        if not elm:
            return
        # 0:id, 1:uid, 2:uname 3:name
        self.user = (await self.dbi.select(self.dbi["User"], elm[4]))()
        self.time = datetime.datetime.strptime(elm[2], "%Y-%m-%d %H:%M:%S.%f%z").strftime("%d/%m/%y %H:%M:%S")
        self.elm = Element(self.chat, self.dbi, elm[0], elm[4], elm[3])

        msg = f"""<div id="m{self.elm.eid}" class="msg">
        <div class="user">
        {await self.head()}
        </div>
        <div class="body {self.elm.ename}">
        {await self.elm}
        </div>
        </div>"""
        return msg

    async def head(self) -> str:
        return ""

class Message(BaseMessage):

    async def head(self) -> str:
        return f"""<button type="button" onclick="chat.msg.eid({self.eid})">
        <img src="{await self.elm.profile_pic(self.user[1])}">
        </button>
        {self.elm.link_user(self.user[2])}
        <p class="time">{self.time}</p>
        <div class="likes">
        {await self.likes()}
        </div>"""

    async def likes(self) -> str:
        users = [(await self.dbi.select(self.dbi["User"], u[2]))() for u in (await self.dbi.select(self.dbi["Like"], db.Condition(self.elm.eid)))(0)]
        images = []
        for user in users:
            images.append(f"""<a class="link" href="https://www.instagram.com/{user[2]}/">
            <img class="like" src="{await self.elm.profile_pic(user[1])}">
            </a>
            """)
        return "".join(images)

class MessageSingle(Message):

    async def head(self) -> str:
        return f"""<a class="link eid" href="/ig/{self.chat.name}/{self.elm.eid}">{self.elm.eid}</a>
        {self.elm.link_user(self.user[2])}
        <p class="time">{self.time}</p>"""

class IGReq(website.Request):

    def init(self, chat: dbc.Chat, eid: int):
        self.chat = chat
        self.eid = eid

    async def handle(self):
        try:
            self.client.header << website.Header("Content-Type", "text/html")
            data = await self.chat.ig.element(self.eid)
            if "media" not in data:
                return self.client.buffer << f"""<p id={self.eid} class="exp">Media Expired</p>"""
            media = data["media"]
            if media["type"] == "image":
                return self.client.buffer << f"""<img id="{self.eid}" src="{media["url"]}">"""
            elif media["type"] == "video":
                return self.client.buffer << f"""
                <video id="{self.eid}" width="{media["size"][0]}" height="{media["size"][1]}" loop controls autoplay muted>
                <source src="{media["url"]}">
                </video>"""
            elif media["type"] == "gif":
                return self.client.buffer << f"""<img id="{self.eid}" src="{media["url"]}">"""
            elif media["type"] == "audio":
                return self.client.buffer << f"""<audio id="{self.eid}" controls>
                <source src="{media["url"]}">
                </audio>"""

        except Exception as e:
            print("Err", data, type(e), e)
        return self.client.buffer << self.err()

    def err(self) -> str:
        return f"""<p id={self.eid} class="err">Error Loading Media</p>"""

class ProfilePic(IGReq):

    async def handle(self):
        self.client.header << website.Header("Content-Type", "text/html")
        return self.client.buffer << f"""<img id={self.eid} class="onload" onload="chat.ext.mda(this, {self.eid}, 'p')" src="{(await self.chat.ig.profile(self.eid))["pfp"]}" onerror="chat.ext.img_err(this)" alt="/img/instagram/default_user.png">"""

class SearchPage(website.Request):

    def init(self, chat: dbc.Chat):
        self.chat = chat

    async def handle(self):
        self.client.buffer << website.buffer.Python(website.path + "page/instagram/search.html", self)

class Search(website.Request):

    BLOCK = 32

    def init(self, chat: dbc.Chat):
        self.chat = chat
        self.dbi = self.chat.db(self.client.session.id+"_search")

    async def handle(self):
        self.page = None
        if "page" in self.client.query:
            self.page = int(self.client.query["page"])

        else:
            user = self.client.query["user"] or False
            text = self.client.query["text"] or False
            date = self.client.query["date"] or False
            page = int(self.client.query["page"]) if "page" in self.client.query else 0

            search = (user, text, date)
            if self.client.session.search["id"] != hash(search):
                res = await self.perform_search(*search)
                if res:
                    self.client.session.search["id"] = hash(search)
                    self.page = page
            else:
                self.page = page

        if self.page is None:
            self.client.buffer << website.buffer.Python(website.path + "page/instagram/result_err.html", self)
        else:
            # self.client.header << website.Header("Cache-Control", "public, max-age=900", "immutable")
            self.client.buffer << website.buffer.Python(website.path + "page/instagram/result.html", self)

    async def perform_search(self, user: str, text: str, date: str):
        if user:
            u = f"{user}%"
            tbla, tblb = self.dbi["User"], self.dbi["User Active"]
            await self.dbi.select(db.Join(tbla, tblb[1]), db.Condition(u, tbla[2], db.op.LIKE), db.op.OR, db.Condition(u, tbla[3], db.op.LIKE), cols=(tbla[0],))
            user = self.dbi.fetch()
            if not user:
                self.client.session.search["err"] = f"User does not exist"
                return False
            else:
                user = user[0]

        tbla, tblb = self.dbi["Element"], self.dbi["Text"]
        cond = []
        if user:
            cond.append(db.Condition(user, tbla["user"]))
        if date:
            cond.append(db.Condition(f"{date}%", tbla["time"], db.op.LIKE))
        if text:
            if text.startswith("!"):
                etype, ename = (await self.dbi.select(self.dbi["Element Type"], db.Condition(f"%{text.split(' ')[0][1:].split('!')[0]}%", 1, op=db.op.LIKE)))()
                tblb = self.dbi[ename]
            else:
                etype = 1
                cond.append(db.Condition(f"%{text}%", tblb["text"], db.op.LIKE))
        else:
            etype = 1
        await self.dbi.select(db.Join(tbla, tblb[1]), *cond, cols=(tbla[0],))
        res = self.dbi.fetch(0)
        if not res:
            self.client.session.search["err"] = "No results"
            return False
        self.client.session.search["data"] = [i[0] for i in res]
        self.client.session.search["size"] = len(self.client.session.search["data"])
        self.client.session.search["pages"] = self.client.session.search["size"] // self.BLOCK - (not self.client.session.search["size"] % self.BLOCK)
        return True

    async def result(self) -> str:
        start = min(self.client.session.search["size"], self.BLOCK * self.page)
        end = min(start + self.BLOCK, self.client.session.search["size"])
        data = await Interface.gather(*(MessageSingle(self.client, self.request, self.seg, self.chat, self.dbi, elm) for elm in self.client.session.search["data"][start:end]))
        return "<hr>".join(data)

class Save(website.Request):

    def init(self, chat: dbc.Chat):
        self.chat = chat
        self.dbi = self.chat.db(self.client.session.id)

    async def handle(self):
        if "s" in self.client.query:
            eid = int(self.client.query["elm"])
            if not (await self.dbi.select(self.dbi["elm save"], db.Condition(eid)))():
                await self.dbi.insert(self.dbi["elm save"], eid)
            return

        return self.client.buffer << website.buffer.Python(f"{website.path}page/instagram/save.html", self)

    async def elements(self) -> str:
        elements = (await self.dbi.select(self.dbi["elmsave"]))(0)
        data = await Interface.gather(*(MessageSingle(self.client, self.request, self.seg, self.chat, self.dbi, elm[1]) for elm in elements))
        return "<hr>".join(filter(None, data))

class Media(website.Request):

    def init(self, chat: dbc.Chat):
        self.chat = chat
        self.dbi = self.chat.db(self.client.session.id)

    async def handle(self):
        pass