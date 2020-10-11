from database import db
from path import PATH

DB_FILENAME = f"{PATH}../../resource/database/poppy_tester.save.db"

database = db.Database(DB_FILENAME)

with database:
    dbi = database()
    # database.table("elmsave", db.Column.Foreign("eid", database["Element"]))