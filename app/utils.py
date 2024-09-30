import json
from pathlib import Path

def check_file(file):
    path = Path('../mind_bot/json/' + file)
    if path.exists():
        with open(path, 'r', encoding='utf-8') as info:
            try:
                data = json.load(info)
            except json.JSONDecodeError:
                data = []
    else:
        data = []
    return data

def is_admin(chat_id) -> bool:
    admins = check_file('admins.json')
    return chat_id == admins["Admin Id-number"]
