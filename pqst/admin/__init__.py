import caching
import website
import urllib.request
from interface import Interface

log = website.log.page("admin")

class ARequest(website.Request):
    async def handle(self):
        self.client.buffer << website.buffer.Python(f"{website.path}page/admin/default.html", self)
    async def extra(self):
        return ""

class ClearCache(ARequest):
    async def handle(self):
        caching.Manager.timeout()
        await super().handle()
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
    async def extra(self):
        return f"<p>Redirection Status: {self.state}<p>"
class EnableServerRedirect(RedirectStatus):
    async def handle(self):
        await RedirectStatus.change(True)
        await super().handle()
class DisableServerRedirect(RedirectStatus):
    async def handle(self):
        await RedirectStatus.change(False)
        await super().handle()

class Shutdown(ARequest):
    async def extra(self):
        log.critical("Server Shutdown Request", self.client)
        async def timeout():
            await Interface.next(1)
            Interface.stop()
        Interface.schedule(timeout())
        return "Shutting Down Server"

class Index(website.Request):
    cfg = website.config("admin.key")
    async def handle(self):
        if self.client.query.get("q", None) == self.cfg["admin"]["key"]:
            return self.client.buffer <<  website.buffer.Python(f"{website.path}page/admin/index.html", self)
        self.client.buffer << website.buffer.Python(f"{website.path}page/404Error.html", self)

    @website.buffer.wrap
    def data(self):
        return f"/{'/'.join(self.request)}"

    async def get_pages(self) -> str:
        links = []
        for n,l in self.pages.items():
            links.append(f"""<a class="link page" href="/key/{l}">{n}</a>""")
        return "".join(links)

    pages = {
        "Kill Server": "exit",
        "Purge Caches": "cache",
    }

request = website.Tree(
    Index, Index,
    exit=Shutdown,
    cache=ClearCache,
    redirect=website.Tree(
        RedirectStatus, RedirectStatus, RedirectStatus,
        enable=EnableServerRedirect,
        disable=DisableServerRedirect,
    )

)
RedirectStatus._redirect.insert("key", request)
