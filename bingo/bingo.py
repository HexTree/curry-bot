from bingo.bingosync import *
import random


def get_room(name=None):
    with open('bingo/bingo_cards.json', 'r') as f:
        data = f.read()

    # decide password
    with open('bingo/passphrases.txt', 'r') as f:
        passphrase = random.choice(f.readlines()).strip()

    # create room at bingosync
    room_url = create_room(name if name else "Azure Dreams", passphrase, data)
    print(room_url, passphrase)
    return room_url, passphrase
