import website
import importlib
from .home import request as home
from collections import defaultdict

__default = home

program: dict[str, website.Request] = defaultdict(lambda: __default)

for __name in website.config("server.cfg")["program"].keys():
    try:
        __mod = importlib.import_module(f".{__name}", "pqst")
        __req = program[__name] = __mod.request
        website.log._create(__name, __req.log_format if hasattr(__req, "log_format") else None)
    except (ImportError, AttributeError):
        program[__name] = __default
