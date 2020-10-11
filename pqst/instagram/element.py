import website
import database as db
from interface import Interface
from .dbc import Chat
from . import igapi

import traceback

class OElement:

    def __init__(self, chat: Chat, dbc, eid: int, usr: int, etype: (str, int), client: website.Client):
        self.chat, self.dbc, self.client = chat, dbc, client
        self.eid, self.usr = eid, usr
        self.etype = etype
        try:
            self.__func, self.ename = self._proc_elm_type[self.etype]
        except KeyError:
            self.__func, self.ename = self._proc_elm_type[0]

    def __await__(self):
        return self.compile().__await__()

    async def compile(self) -> str:
        try:
            return await self.__func(self)
        except KeyError:
            return await self.__func(self)

    __call__ = compile

    async def e_error(self) -> str:
        elm = (await self.dbc.select(self.dbc["Element"], self.eid))()
        type_name = (await self.dbc.select(self.dbc["Element Type"], elm[3]))()
        return f"<p class=\"err\">Type: {elm[3]} = {type_name[1]}</p>"

    async def e_text(self) -> str:
        elm = (await self.dbc.select(self.dbc["Text"], db.Condition(self.eid)))()
        link = (await self.dbc.select(self.dbc["ElmTypeLink"], db.Condition(elm[0])))(0)
        text = elm[2]
        if link:
            for count, l in enumerate(link):
                text = text.replace(l[2], f"""<a class="link txt" href="{{{count}}}">{{{count}}}</a>""", 1)
            text = text.format(*map(lambda x: x[2], link))
        return text

    async def e_action(self) -> str:
        elm = (await self.dbc.select(self.dbc["ElmTypeAction"], db.Condition(self.eid)))()
        stype = elm[2]
        msg = elm[3]
        if stype == "c": # Call
            msg = "Started" if msg == "s" else "Ended"
            return f"<p>{msg}</p><p class=\"head\"> Video Call</p>"
        elif stype == "n": # Renaming the Group Chat
            return f"<p class=\"head\">Name:</p><p> {msg}</p>"
        elif stype in ("a", "r"): # Add/Remove User
            stype = "Add" if stype == "a" else "Remove"
            try:
                uid = int(msg)
                u = (await self.dbc.select(self.dbc["User"], db.Condition(uid)))()
                if u:
                    msg = u[2]
            except ValueError:
                pass
            return f"<p class=\"head\">{stype} User:</p><p> {self.link_user(msg)}</p>"

    async def e_placeholder(self) -> str:
        elm = (await self.dbc.select(self.dbc["ElmTypePlaceholder"], db.Condition(self.eid)))()
        if elm[2] == "s":
            stype = "Story"
            msg = "Expired"
        else:
            stype = {"p": "Post", "i": "Image", "v": "Video"}[elm[2]]
            if " deleted" in elm[3]:
                msg = "Deleted"
            elif " private" in elm[3]:
                sta = elm[3].find("@")
                end = elm[3].find(" has")
                acc = elm[3][sta+1:end]
                msg = f"Private {self.link_user(acc, True)}"
            else:
                msg = "Unavailable"
        return f"{stype} {msg}"

    async def e_media(self) -> str:
        elm = (await self.dbc.select(self.dbc["ElmTypeMedia"], db.Condition(self.eid)))()
        return f"""<p class="igdata onload" onload="chat.ext.mda(this, {self.eid}, 'm')" alt="Failed to Load IG Data">Loading IG Data...</p>"""

        # return await self.e_error()

    async def e_share(self) -> str:
        try:
            author, code, stype, msg = (await self.dbc.select(self.dbc["ElmTypeShare"], db.Condition(self.eid), cols=(2, 3, 4, 5)))()
            uid, uname = (await self.dbc.select(self.dbc["User"], author, cols=(1, 2)))()
            if stype == "p":
                if msg:
                    text = msg
                    index = text.index("\n") if "\n" in text else 80
                    text = [text[:index], text[index:].replace("\n", "\\n")] if len(text) > index else [text, False]
                    main, hidden = text[0], f"<p class=\"show_more\" onclick=\"chat.msg.shr_more(this, \'{text[1]}\')\"> more</p>" if text[1] else ""
                    msg = f"""
                    <div class="txt"><p>{main}</p>{hidden}</div>
                    """
                else:
                    msg = ""
                return f"""
                <div class="usr">
                    <img class=\"onload\" onload=\"chat.ext.mda(this, {uid}, 'p')\" src="/img/instagram/default_user.png">
                    {self.link_user(uname)}
                </div>
                <a class="link pst" href="https://instagram.com/p/{code}/">
                    <img class="post" src="https://instagram.com/p/{code}/media/?size=l" alt="This Post is Private" onerror="chat.ext.mda_err(this)">
                </a>{msg}"""
        except Exception as e:
            traceback.print_exception(e, e, e.__traceback__)
            return await self.e_error()

    def link_user(self, username: str, at: bool=False) -> str:
        return f"<a class=\"link usr\" href=\"https://www.instagram.com/{username}/\">{'@' if at else ''}{username}</a>"

    _proc_elm_type = {
        0: (e_error, "err"),
        1: (e_text, "txt"),
        2: (e_action, "act"),
        3: (e_placeholder, "plh"),
        4: (e_media, "mda"),
        5: (e_share, "shr"),

        # 0: e_error,
        # 1: e_text,
        # 2: e_action,
        # 3: e_placeholder,
        # 4: e_media,
        # 5: e_share,
    }

class Element:

    def __init__(self, chat: Chat, dbi, eid: int, usr: int, etype: int):
        self.chat, self.dbi = chat, dbi
        self.eid, self.usr = eid, usr
        self.etype = etype
        try:
            self.__func, self.ename = self._proc_elm_type[self.etype]
        except KeyError:
            self.__func, self.ename = self._proc_elm_type[0]

    def __await__(self):
        return self.compile().__await__()
    async def compile(self) -> str:
        try:
            return await self.__func(self)
        except KeyError:
            raise

    def link_user(self, username: str, at: bool=False) -> str:
        return f"<a class=\"link usr\" href=\"https://www.instagram.com/{username}/\">{'@' if at else ''}{username}</a>"

    async def out_error(self):
        type_name = (await self.dbi.select(self.dbi["Element Type"], self.etype))()
        return f"<p class=\"err\">Type: {self.etype} = {type_name[1]}</p>"

    async def out_text(self) -> str:
        text = (await self.dbi.select(self.dbi["Text"], db.Condition(self.eid)))()
        links = (await self.dbi.select(self.dbi["ElmTypeLink"], db.Condition(text[0])))(0)
        text = text[2]
        if links:
            links = [l[2] for l in links]
            for count, link in enumerate(links):
                text = text.replace(link, f"""<a class="link txt" href="{{{count}}}">{{{count}}}</a>""", 1)
            text = text.format(*links)
        return text

    async def out_action(self) -> str:
        elm = (await self.dbi.select(self.dbi["ElmTypeAction"], db.Condition(self.eid)))()
        stype = elm[2]
        msg = elm[3]
        if stype == "c": # Call
            msg = "Started" if msg == "s" else "Ended"
            return f"<p>{msg}</p><p class=\"head\"> Video Call</p>"
        elif stype == "n": # Renaming the Group Chat
            return f"<p class=\"head\">Name:</p><p> {msg}</p>"
        elif stype in ("a", "r"): # Add/Remove User
            stype = "Add" if stype == "a" else "Remove"
            try:
                uid = int(msg)
                u = (await self.dbi.select(self.dbi["User"], db.Condition(uid)))()
                if u:
                    msg = u[2]
            except ValueError:
                pass
            return f"<p class=\"head\">{stype} User:</p><p> {self.link_user(msg)}</p>"

    async def out_placeholder(self) -> str:
        elm = (await self.dbi.select(self.dbi["ElmTypePlaceholder"], db.Condition(self.eid)))()
        if elm[2] == "s":
            stype = "Story"
            msg = "Expired"
        else:
            stype = {"p": "Post", "i": "Image", "v": "Video"}[elm[2]]
            if " deleted" in elm[3]:
                msg = "Deleted"
            elif " private" in elm[3]:
                sta = elm[3].find("@")
                end = elm[3].find(" has")
                acc = elm[3][sta+1:end]
                msg = f"Private {self.link_user(acc, True)}"
            else:
                msg = "Unavailable"
        return f"{stype} {msg}"

    async def out_media(self) -> str:
        elm = (await self.dbi.select(self.dbi["ElmTypeMedia"], db.Condition(self.eid)))()
        return f"""<p class="igdata onload" onload="chat.ext.mda(this, {self.eid}, 'm')" alt="Failed to Load IG Data">Loading IG Data...</p>"""

    async def out_share(self) -> str:
        try:
            author, code, stype, msg = (await self.dbi.select(self.dbi["ElmTypeShare"], db.Condition(self.eid), cols=(2, 3, 4, 5)))()
            uid, uname = (await self.dbi.select(self.dbi["User"], author, cols=(1, 2)))()
            if stype == "p":
                if msg:
                    text = msg
                    index = text.index("\n") if "\n" in text else 80
                    text = [text[:index], text[index:].replace("\n", "\\n")] if len(text) > index else [text, False]
                    main, hidden = text[0], ""
                    if text[1]:
                        text[1] = text[1].replace("'", "\\'").replace('"', '\\"')
                        hidden = f"""<p class="show_more" onclick="chat.msg.shr_more(this, '{text[1]}')"> more</p>"""
                    msg = f"""
                    <div class="txt"><p>{main}</p>{hidden}</div>
                    """
                else:
                    msg = ""
                return f"""<div class="usr">
                <img class=\"onload\" onload=\"chat.ext.mda(this, {uid}, 'p')\" src="/img/instagram/default_user.png">
                    {self.link_user(uname)}
                </div>
                <a class="link pst" href="https://instagram.com/p/{code}/">
                    <img class="post" src="https://instagram.com/p/{code}/media/?size=l" alt="This Post is Private" onerror="chat.ext.mda_err(this)">
                </a>{msg}"""
            elif stype == "u":
                return f"""<div class="usr">
                <img class=\"onload\" onload=\"chat.ext.mda(this, {uid}, 'p')\" src="/img/instagram/default_user.png">
                    {self.link_user(uname, True)}
                </div>
                """
            else:
                raise ValueError(stype)
        except Exception as e:
            traceback.print_exception(e, e, e.__traceback__)
            return await self.out_error()

    async def profile_pic(self, uid: int):
        return (await self.chat.ig.profile(uid))["pfp"]

    _proc_elm_type = {
        0: (out_error, "err"),
        1: (out_text, "txt"),
        2: (out_action, "act"),
        3: (out_placeholder, "plh"),
        4: (out_media, "mda"),
        5: (out_share, "shr"),
    }
