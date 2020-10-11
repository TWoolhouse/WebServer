# text
    # placeholder
    # action
# story
# call

# Media
    # image
    # video
    # gif
    # audio

# share
# link
# profile
# tv

### Types ###

# text
# action
# placeholder
# link
# like
# story
# profile
# live
# call
# media
    # image # Req
    # video # Req
    # gif
    # audio # Req
# share
    # image # Req
    # video # Req
    # carousel # Req


"""
{
    'text': 1,
    'action': 2,
    'share_image': 3,
    'image': 4,
    'like': 5,
    'share_video': 6,
    'link': 7,
    'placeholder': 8,
    'story': 9,
    'video': 10,
    'audio': 11,
    'share_carousel': 12,
    'profile': 13,
    'call': 14,
    'share_undefined': 15,
    'gif': 16,
    'live_invite': 17,
    'tv': 18
}
"""

import enum
import database as db

@enum.unique
class ElmType(enum.IntEnum):
    TEXT = 1
    ACTION = 2
    PLACEHOLDER = 3
    MEDIA = 4
    LIKE = 5
    LINK = 6
    PROFILE = 7
    SHARE = 8

    STORY = 9
    LIVE = 10

    TV = 11
    CALL = 12

class MdaType(enum.IntEnum):
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3
    GIF = 4
    CAROUSEL = 5

"""

class User:

    def __init__(self, id: int, username: str, text: str, pfp: str):
        self.id = id
        self.username = username
        self.text = text
        self.pfp = pfp

class Element:

    def __init__(self, id: str, user: User, timestamp: int, reaction: list=[]):
        self.id = id
        self.user = user
        self.time = timestamp
        self.reaction = reaction

class Text(Element):

    def __init__(self, id: str, user: User, timestamp: int, text: str, reaction: list=[]):
        super().__init__(id, user, timestamp, reaction)
        self.text = text

class Placeholder(Text):

    def __init__(self, id: str, user: User, timestamp: int, title: str, text: str, reaction: list=[]):
        super().__init__(id, user, timestamp, text, reaction)
        self.title = title

class Action(Text):
    pass

class Story(Element):
    pass

class Call(Element):
    def __init__(self, id: str, user: User, timestamp: int, type: str, reaction: list=[]):
        super().__init__(id, user, timestamp, reaction)
        self.type = type

class Media(Element):
    pass

"""