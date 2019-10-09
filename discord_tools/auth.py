import json


def get_token():
    with open('discord_tools/creds.json', 'r') as f:
        return json.load(f)['token']