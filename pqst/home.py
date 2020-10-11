import website

class HomeRequest(website.Request):

    async def handle(self):
        self.client.buffer << website.buffer.Python(f"{website.path}page/home.html", self)

request = HomeRequest