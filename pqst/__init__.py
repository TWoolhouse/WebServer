from .home import request as home

__default = home

try:
    from .admin import request as admin
except ImportError:
    admin = __default

try:
    from .instagram import request as igdb
except ImportError:
    igdb = __default

try:
    from .volume import request as volume
except ImportError:
    volume = __default

try:
    from .cupboard import request as cupboard
except ImportError:
    cupboard = __default

try:
    from .clothing import request as clothing
except ImportError:
    clothing = __default