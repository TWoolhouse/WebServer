import json
import os
import time
from path import PATH
from interface import Interface
import database as db

USERNAME = "__bot__dinoswar_powa"
PASSWORD = "t9JZQmWA6BHzAkf"

ITERATIONS = 1000
CHAT_NAME = "Poppy Tester"
# CHAT_NAME = "Lani Best Girl"
IG_PATH = "C:/dev/Code/Node/Project/Instagram/"
IG_DIRECTORY = f"{IG_PATH}chat/{CHAT_NAME}/"

import debug
# debug.enable()

@debug.call
def read_json(filename: str) -> dict:
    with open(filename, encoding="utf8") as file:
        return json.load(file)

def get_folders() -> str:
    messages = IG_DIRECTORY+"message/"
    try:
        folders = sorted(os.listdir(messages))
    except FileNotFoundError:
        return
    for folder in folders:
        yield messages+folder+"/"

@debug.catch
def read_folder(folder: str) -> list:
    items = []
    for filename in os.listdir(folder):
        item = read_json(folder+filename)
        if isinstance(item, list):
            items.extend(item)
        else:
            items.append(item)
    try:
        items.sort(key=lambda x: x["time"])
    except Exception as e:
        print(items)
        raise e
    return items

@debug.log
def current_cursor() -> str:
    try:
        recent = read_folder(list(get_folders())[-1])[-1]
        return recent["id"]
    except IndexError:
        return "MINCURSOR"

@debug.log
def final_cursor() -> str:
    try:
        old = read_folder(next(get_folders()))[0]
        return old["id"]
    except IndexError:
        return "0"

@debug.log
def execute_crawler(end=False):
    os.makedirs(IG_DIRECTORY, exist_ok=True)
    cursor = f"-s {final_cursor()}" if end else f"-c {current_cursor()}"
    cmd = f"node {IG_PATH}main.js {USERNAME} {PASSWORD} {cursor} -d \"{IG_DIRECTORY}\" -n \"{CHAT_NAME}\" -i {ITERATIONS // 10}"
    start = time.time()
    os.system(cmd)
    end = time.time()
    seconds = end-start
    print(f"Time Taken: {int(seconds)}")
    return seconds

def read_meta():
    messages = IG_DIRECTORY+"message/meta/"
    try:
        folders = sorted(os.listdir(messages))
    except FileNotFoundError:
        return
    for folder in folders:
        yield messages+folder

def read_all() -> dict:
    for f in read_meta():
        yield from read_json(f)

def merge_folder(folder: str, name: str):
    with open(IG_DIRECTORY+"message/meta/"+name, "w", encoding="utf-8") as file:
        json.dump(read_folder(folder), file)

@debug.log
@debug.time
def merge_data():
    print("Merging Files")
    length = len(IG_DIRECTORY+"message/")
    os.makedirs(IG_DIRECTORY+"message/meta/", exist_ok=True)
    for i, f in enumerate(get_folders()):
        name = f[length:-1]
        if name != "meta":
            print(i, name)
            merge_folder(f, name)
    print("Merged")

execute_crawler()
merge_data()