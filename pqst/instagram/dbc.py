import website
import database as db
from . import igapi
from interface import Interface

class Chat:
    def __init__(self, name: str, db_name: str, pwd: str, chat_name: str):
        self.name = name
        self.password = pwd
        self.db = db.DatabaseAsync(f"{website.path}resource/database/{db_name}.save.db")
        self.db.open()
        self.ig = igapi.IGData(self.db("API"), chat_name)

chat = {
    "PoppyTester": Chat("PoppyTester", "poppy_tester", "ptlol", "Poppy Tester"),
}