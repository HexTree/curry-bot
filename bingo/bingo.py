from bingo.bingosync import *

import csv
import json
import random


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
    # create cards from csv
    cards = []
    with open('bingo/bingo_cards.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_num = 0
        for row in csv_reader:
            line_num += 1
            if line_num == 1:
                continue
            card = Card(row[0], row[1], row[2])
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
