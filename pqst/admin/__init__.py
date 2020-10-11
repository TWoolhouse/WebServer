from interface import Interface
from caching import Cache
import website
import urllib.request

class ARequest(website.Request):
    async def extra(self):
        return ""

class ClearCache(ARequest):
    async def handle(self):
        Cache.reset()
        self.client.buffer << website.buffer.Python(f"{website.path}page/admin/default.html", self)
    async def extra(self):
        return """<p>Clear all the Caches</p>"""

class RedirectStatus(ARequest):
    root = website.Request
    state = False
    _tree = None
    _redirect = website.Tree(
        *[website.Request.redirect(hostname="192.168.1.111", port=53331, scheme="https")]*3,
    )
    @classmethod
    async def change(cls, state: bool):
        if state:
            try:
                await Interface.process(urllib.request.urlopen, "http://192.168.1.111:53335/")
            except urllib.error.URLError:
                state = False
        if state:
            cls._tree, cls.root.tree = cls.root.tree, cls._redirect
        elif cls._tree:
            cls.root.tree = cls._tree
        cls.state = state
    async def handle(self):
        self.client.buffer << website.buffer.Python(f"{website.path}page/admin/default.html", self)
    async def extra(self):
        return f"<p>Redirection Status: {self.state}<p>"
class EnableServerRedirect(RedirectStatus):
    async def handle(self):
        await RedirectStatus.change(True)
        self.client.buffer << website.buffer.Python(f"{website.path}page/admin/default.html", self)
class DisableServerRedirect(RedirectStatus):
    async def handle(self):
        await RedirectStatus.change(False)
        self.client.buffer << website.buffer.Python(f"{website.path}page/admin/default.html", self)

request = website.Tree(
    cache=ClearCache,
    redirect=website.Tree(
        RedirectStatus, RedirectStatus, RedirectStatus,
        enable=EnableServerRedirect,
        disable=DisableServerRedirect,
    )
)
RedirectStatus._redirect.insert("key", request)