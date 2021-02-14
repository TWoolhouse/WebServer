import website
from interface import Interface
import sound
import sinput
# from . import music_player as player

class Command(website.Request):

    controller = sound.Volume(10)

    async def handle(self):
        if "v" in self.client.query:
            self.tree[self.client.query["v"]](self)
        self.client.buffer << website.buffer.Json({"volume": self.controller.volume()})

    def vol(self):
        cmd = self.client.query["c"]
        try:
            amt = int(self.client.query["amt"])
        except ValueError:
            amt = None

        if cmd == "scrub":
            if amt:
                self.controller.up(amt)
        elif cmd == "set":
            if amt is not None:
                self.controller.set(amt)
        elif cmd == "sync":
            self.controller.sync(amt)
        elif cmd == "media":
            if amt == 0:
                sound.Media.pause()
            elif amt == 1:
                sound.Media.next()
            elif amt == 2:
                sound.Media.prev()

    def yt(self):
        cmd = self.client.query["c"]
        drc = self.client.query["dir"]
        try:
            amt = int(self.client.query["amt"])
        except ValueError:
            amt = None

        sinput.modify(sinput.keys.SHIFT, sinput.key)(sinput.keys.N)

    tree = {
        "vol": vol,
        "yt": yt,
    }

class Home(website.Request):
    async def handle(self):
        self.client.buffer << website.buffer.Python(website.path+"page/volume/home.html", self)
    # class Youtube(website.Request):
    #     async def handle(self):
    #         self.client.buffer << website.buffer.Python(website.path+"page/volume/youtube.html", self)
    # class Spotify(website.Request):
    #     async def handle(self):
    #         self.client.buffer << website.buffer.Python(website.path+"page/volume/spotify.html", self)
    # class Groove(website.Request):
    #     async def handle(self):
    #         self.client.buffer << website.buffer.Python(website.path+"page/volume/groove.html", self)

# class RootRequest(website.Request):

#     async def handle(self):
#         return await self.tree(self)

request = website.Tree(
    Home,
    end__=Home,
    default__=Home,
    cmd=Command,
    # upload=player.Uploader,
    # player=player.Home,
    # youtube=Home.Youtube,
    # spotify=Home.Spotify,
    # groove=Home.Groove
)
