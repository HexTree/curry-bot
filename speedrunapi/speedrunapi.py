import srcomapi
import srcomapi.datatypes as dt
from difflib import SequenceMatcher

api = srcomapi.SpeedrunCom()
api.debug = 1
game = api.search(srcomapi.datatypes.Game, {"name": "azure dreams"})[0]


def fetch_leaderboard(query):
    best_guess = max(game.categories, key=lambda cat: SequenceMatcher(None, query.lower(), cat.name.lower()).ratio())
    yield best_guess.name
    for r in dt.Leaderboard(api, data=api.get("leaderboards/{}/category/{}?embed=variables".format(game.id, best_guess.id))).runs:
        yield r['place'], r['run'].players[0].name, r['run'].times['primary_t']
