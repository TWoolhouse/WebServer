import time
import debug
from path import PATH
from interface import Interface
import os.path
from .instagram_private_api import Client, ClientError
import asyncio
import codecs
import json
import functools
import multiprocessing as mp
from caching import cache

USERNAME = "__bot__dinoswar_powa"
PASSWORD = "t9JZQmWA6BHzAkf"
SETTING_FILE = PATH+"pqst/instagram/igkey.json"
# SETTING_FILE = PATH+"igkey.json"

# def cache(func):
#     data = func
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         nonlocal data
#         if data == func:
#             data = func(*args, **kwargs)
#         return data
#     return wrapper

class __API:

    def __init__(self):
        self.open()

    @staticmethod
    def __to_json(python_object):
        if isinstance(python_object, bytes):
            return {'__class__': 'bytes',
                    '__value__': codecs.encode(python_object, 'base64').decode()}
        raise TypeError(repr(python_object) + ' is not JSON serializable')
    @staticmethod
    def __from_json(json_object):
        if '__class__' in json_object and json_object['__class__'] == 'bytes':
            return codecs.decode(json_object['__value__'].encode(), 'base64')
        return json_object

    def __onlogin_callback(self, api):
        cache_settings = api.settings
        with open(SETTING_FILE, 'w') as outfile:
            json.dump(cache_settings, outfile, default=self.__to_json)
            debug.print(f"API Saving Auth Settings: {SETTING_FILE}")

    def open(self) -> "API":
        device_id = None
        try:
            if not os.path.isfile(SETTING_FILE):
                debug.print(f"API Unable to find Auth file: {SETTING_FILE}")
                self.api = Client(USERNAME, PASSWORD, on_login=self.__onlogin_callback)
            else:
                with open(SETTING_FILE) as file_data:
                    cached_settings = json.load(file_data, object_hook=self.__from_json)
                debug.print(f"API Reusing Auth Settings: {SETTING_FILE}")
                device_id = cached_settings.get("device_id")
                self.api = Client(USERNAME, PASSWORD, settings=cached_settings)
        except (ClientError) as err:
            debug.print(f"API Client Expired: {err}")
            self.api = Client(USERNAME, PASSWORD, device_id=device_id, on_login=self.__onlogin_callback)
        return self

    @functools.cached_property
    def inbox(self) -> dict:
        return {thread["thread_title"]: {"id": thread["thread_id"]} for thread in self.api.direct_v2_inbox()["inbox"]["threads"]}

    def element(self, thread: str, elm_id: str) -> dict:
        return self.api._call_api(f"direct_v2/threads/{thread}/?cursor={elm_id}&limit=1&visual_message_return_type=unseen")["thread"]["items"][0]

    def profile(self, uid: int) -> dict:
        try:
            return self.api._call_api(f"users/{uid}/info/")["user"]
        except ClientError:
            return {
                "pk": 0,
                "username": str(None),
                "full_name": str(None),
                "profile_pic_url": "/img/instagram/default_user.png",
            }

API = __API()

class IGData:

    def __init__(self, dbi, name: str):
        self.__dbi = dbi
        self.__chat_name = name
        self.__thread_id = API.inbox[name]["id"]
        # self.__cache_data = {
        #     "elm": {},
        #     "profile": {},
        # }

    """def cache(ctype: str):
        def cache(func):
            async def cache(self, key: int, *args, **kwargs) -> dict:
                cdict = self.__cache_data[ctype]
                if key in cdict:
                    data = cdict[key]
                    if isinstance(data[1], asyncio.Event):
                        await data[1].wait()
                        return data[1]
                    data[0] = time.time_ns()
                    return data[1]
                data = cdict[key] = [time.time_ns(), asyncio.Event()]
                res = await func(self, key, *args, **kwargs)
                data[1].set()
                data[1] = res
                return res
            return cache
        return cache"""

    # @cache("profile")
    @cache
    @debug.call
    async def profile(self, user_id: int) -> str:
        profile = await Interface.process(API.profile, user_id)
        return {
            "id": profile["pk"],
            "username": profile["username"],
            "name": profile["full_name"],
            "pfp": profile["profile_pic_url"],
        }

    # @cache("elm")

    @cache
    @debug.call
    async def element(self, elm_id: int) -> dict:
        ig_id = (await self.__dbi.select(self.__dbi["Element"], elm_id+1))()[1]
        return self.__element_type_process(await Interface.process(API.element, self.__thread_id, ig_id))

    def __element_type_process(self, element: dict) -> dict:
        data = {}
        etype = element["item_type"]
        if etype in ("media", "raven_media", "animated_media", "voice_media"):
            if etype == "media":
                e = element["media"]
            elif etype == "raven_media":
                e = element["visual_media"]["media"]
            elif etype == "animated_media":
                e = element["animated_media"]["images"]["fixed_height"]
                e["media_type"] = 3
            elif etype == "voice_media":
                e = element["voice_media"]["media"]
            data["media"] = self.__etp_media(e)
            element["type"] = "media"

        return data

    def __etp_media(self, e: dict) -> dict:
        data = {}
        try:
            if e["media_type"] == 1: # Image
                m = e["image_versions2"]["candidates"][0]
                data["type"] = "image"
                data["size"] = (m["width"], m["height"])
                data["url"] = m["url"]
            elif e["media_type"] == 2: # Video
                data["type"] = "video"
                m = e["video_versions"][0]
                data["size"] = (m["width"], m["height"])
                data["url"] = m["url"]
            elif e["media_type"] == 11: # Audio
                data["type"] = "audio"
                data["url"] = e["audio"]["audio_src"]
            elif e["media_type"] == 3: # GIF:
                data["type"] = "gif"
                data["size"] = (e["width"], e["height"])
                data["url"] = e["url"]
        except KeyError:
            return None
        return data