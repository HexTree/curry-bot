import srcomapi
import srcomapi.datatypes as dt

VALID_CATEGORIES = {'Any%', 'Bookless%', '100%'}

api = srcomapi.SpeedrunCom()
api.debug = 1
game = api.search(srcomapi.datatypes.Game, {"name": "azure dreams"})[0]


def fetch_leaderboard(cat):
    if cat not in VALID_CATEGORIES:
        return

    for category in game.categories:
        if cat == category.name:
            break
    else:
        return

    runs = dt.Leaderboard(api, data=api.get("leaderboards/{}/category/{}?embed=variables".format(game.id, category.id))).runs
    return [(r['place'], r['run'].players[0].name, r['run'].times['primary_t']) for r in runs]
