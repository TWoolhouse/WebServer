import website
import secrets
from interface import Interface

from . import dbc
from . import chat as rchat

class Session(website.Session):
    
    def __init__(self, id: str):
        if id is None:
            id = secrets.token_urlsafe(32)
        super().__init__(id)
        self.chats = set()
        self.search = {"id": 0}
        self.eid = 1

class Login(website.Request):

    async def handle(self):
        chat = self.request[self.seg-1] # or self.client.query["chatname"].title().replace("+", "").replace("%20", "")

        if chat not in self.client.session.chats: # Login
            if "chatpassword" not in self.client.query or chat not in dbc.chat or self.client.query["chatpassword"] != dbc.chat[chat].password:
                return Home(self.client, self.request, self.seg)
            self.client.session.chats.add(chat)
        chat = dbc.chat[chat]

        if "msg" in self.client.query: # Message Request
            elms = self.client.query["elm"].split(";")
            dbi = chat.db(self.client.session.id)
            data = await Interface.gather(*(rchat.Message(self.client, self.request, self.seg, chat, dbi, int(eid)) for eid in elms))
            self.client.header << website.Header("Content-Type", "text/html")
            self.client.buffer << "\n".join(filter(None, data))
            if elms:
                self.client.session.eid = int(elms[-1])
            return

        if "ig" in self.client.query: # IG Request
            coro = []
            for mtype, eid in [(i[0], i[1:]) for i in self.client.query["elm"].split(";")]:
                if mtype == "m":
                    coro.append(rchat.IGReq(self.client, self.request, self.seg, chat, int(eid)))
                elif mtype == "p":
                    coro.append(rchat.ProfilePic(self.client, self.request, self.seg, chat, int(eid)))
            return await Interface.gather(*coro)

        try:
            self.client.query["elm"] = int(self.request[self.seg])
        except (IndexError, ValueError):
            if "elm" not in self.client.query:
                self.client.query["elm"] = self.client.session.eid

        # try:
        return self.tree.traverse(self.request, self.seg, self.client, chat)
        # except website.error.TreeTraversal:

    tree = website.Tree(
        rchat.Chat,
        rchat.Chat,
        default__=rchat.Chat,
        search = rchat.SearchPage,
        s = rchat.Search,
        save = rchat.Save,
        media = rchat.Media,
    )

class Home(website.Request):
    async def handle(self):
        self.client.buffer << website.buffer.Python(website.path+"page/instagram/home.html", self)

class RootRequest(website.Request):

    sessions = website.Sessions(Session)
    @website.Request.secure
    async def handle(self):
        self.client.session = self.sessions[self.client.cookie.value("sid")]
        self.client.cookie["sid"] = self.client.session.id
        self.client.cookie["sid"]["path"] = "/ig"
        self.client.cookie["sid"]["Max-Age"] = 86400
        self.client.cookie["sid"]["Secure"] = self.client.cookie["sid"]["HttpOnly"] = True

        return self.tree.traverse(self.request, self.seg, self.client)

    tree = website.Tree(
        Home,
        end__=Home,
        default__=Login,
    )

request = RootRequest