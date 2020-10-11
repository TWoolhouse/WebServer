import debug
# debug.enable()
from interface import Interface
from path import PATH
import website
import database as db
import caching

import pqst
# PI Only
from pqst.admin import RedirectStatus

def stop():
    input()
    Interface.stop()

class CSSRequest(website.Request):

    async def handle(self):
        self.client.header << website.Header("Content-Type", "text/css")
        self.client.header << website.Header("Cache-Control", "public, max-age=604800, immutable")
        await self.load_style("/".join(self.request[1:]))

    async def load_style(self, filename: str):
        data = await website.buffer.File(website.path+"resource/style/"+filename).compile()
        if data.startswith(b"# meta"):
            lines = data.splitlines(False)[1:]
            for index, fname in enumerate(lines, start=1):
                if fname:
                    if fname.startswith(b"# meta"):
                        self.client.buffer << b"\n".join(lines[index+1:])
                        break
                    await self.load_style(fname.decode())
        else:
            self.client.buffer << data

class ImgRequest(website.Request):

    async def handle(self):
        self.client.header << website.Header("Cache-Control", "public, max-age=604800, immutable")
        self.client.header << website.Header("Content-Type", "image/"+self.request[-1].rsplit(".", 1)[-1].lower())
        self.client.buffer << website.buffer.File(website.path+"resource/image/"+"/".join(self.request[1:]))

class JSRequest(website.Request):

    async def handle(self):
        self.client.header << website.Header("Cache-Control", "public, max-age=604800, immutable")
        self.client.header << website.Header("Content-Type", "aplication/javascript", "charset=utf-8")
        self.client.buffer << website.buffer.File(website.path+"resource/js/"+"/".join(self.request[1:]))

class Err404Request(website.Request):

    async def handle(self):

        self.client.status = website.Status.NOT_FOUND
        self.client.buffer << website.buffer.Python(website.path+"page/404Error.html", self)

    @website.buffer.wrap
    def data(self):
        return f"/{'/'.join(self.request)}"

class RootRequest(website.Request):

    @debug.log
    @debug.catch
    async def handle(self) -> website.Request:
        print(f"{self.client.peer}:{self.client.port} /{'/'.join(self.request)} {self.client.query}")
        try:
            return self.tree.traverse(self.request, self.seg, self.client)
        except (website.error.TreeTraversal, website.error.BufferRead):
            return Err404Request(self.client, self.request, self.seg+1)

    tree = website.Tree(
        pqst.home,
        pqst.home,
        key=pqst.admin,
        style=CSSRequest,
        img=ImgRequest,
        js=JSRequest,
        ig=pqst.igdb,
        # vol=pqst.volume,
        cupboard=pqst.cupboard,
        dressme=pqst.clothing,
        **{"favicon.ico": website.buffer.File(f"{website.path}resource/image/favicon.ico")},
    )

RedirectStatus.root = RootRequest

@Interface.submit
async def timeout_test(self):
    caching.Manager.timeout()

if __name__ == "__main__":
    website.buffer.Buffer.cache_disable = True # DEBUG
    server = website.Server(RootRequest, port=53335, ssl=53339)
    # Interface.schedule()
    # Interface.schedule(Interface.process(stop))
    Interface.schedule(server.serve())
    Interface.serve()