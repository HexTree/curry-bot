from googleapi.googleapi import *
from bingo.bingosync import *

import json
import random

CREDS_PATH = 'bingo/creds.json'
SHEET_NAME = 'Azure Dreams Bingo Goals'


class Card:
    def __init__(self, title, desc, length):
        self.title = title
        self.desc = desc
        self.length = length

    def __repr__(self):
        return "Title: {},  Description: {},  Length: {}".format(self.title, self.desc, self.length)

    def get_text(self):
        if not self.desc:
            return self.title
        return "{}: {}".format(self.title, self.desc)


def get_room(name=None):
    # fetch sheet using google api
    sheet = get_sheet(CREDS_PATH, SHEET_NAME)

    # create cards
    cards = []
    for row in sheet.get_all_records(head=2):
        card = Card(row['title'], row['description'], row['length_minutes'])
        if card.title:
            cards.append(card)

    # sample and transform to json
    data = json.dumps([{"name": card.get_text()} for card in random.sample(cards, 25)])
    print(data)

    # decide password
    with open('bingo/passphrases.txt', 'r') as f:
        passphrase = random.choice(f.readlines()).strip()

    # create room at bingosync
    room_url = create_room(name if name else "Azure Dreams", passphrase, data)
    print(room_url, passphrase)
    return room_url, passphrase
