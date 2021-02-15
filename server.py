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

class AudioRequest(website.Request):

    async def handle(self):
        self.client.header << website.Header("Cache-Control", "public, max-age=604800, immutable")
        self.client.header << website.Header("Content-Type", "audio/"+self.request[-1].rsplit(".", 1)[-1].lower())
        self.client.buffer << website.buffer.File(website.path+"resource/audio/"+"/".join(self.request[1:]))

class VideoRequest(website.Request):

    async def handle(self):
        self.client.header << website.Header("Cache-Control", "public, max-age=604800, immutable")
        self.client.header << website.Header("Content-Type", "video/"+self.request[-1].rsplit(".", 1)[-1].lower())
        self.client.buffer << website.buffer.File(website.path+"resource/video/"+"/".join(self.request[1:]))

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
        website.log.request.info(f"/{'/'.join(self.request)}", self.client)
        try:
            return await self.tree.traverse(self)
        except (website.error.TreeTraversal, website.error.BufferRead) as err:
            website.log.request.info(f"/{'/'.join(self.request)} -> FAIL", self.client, exc_info=err)
            return await Err404Request(self)

    tree = website.Tree(
        pqst.home,
        pqst.home,
        js=JSRequest,
        img=ImgRequest,
        audio=AudioRequest,
        video=VideoRequest,
        style=CSSRequest,
        key=pqst.program["admin"],
        hi=pqst.program["hi"],
        ig=pqst.program["instagram"],
        vol=pqst.program["volume"],
        hue=pqst.program["light"],
        candela=pqst.program["candela"],
        coldwater=pqst.program["coldwater"],
        cupboard=pqst.program["cupboard"],
        dressme=pqst.program["clothing"],
        **{
            "favicon.ico": website.buffer.File(f"{website.path}resource/image/favicon.ico"),
        },
    )

RedirectStatus.root = RootRequest

if __name__ == "__main__":
    cfg = website.config("server.cfg")
    # cfg.rwstate.write = True
    cfg.rwstate.write = False
    cfg = cfg["server"]
    website.buffer.Buffer.cache_disable = True # DEBUG
    server = website.Server(RootRequest, port=int(cfg["port"]), ssl=int(cfg["port_ssl"]))
    Interface.schedule(server.serve())
    Interface.main()
