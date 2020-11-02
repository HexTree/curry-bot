import random
import requests

URL = 'http://www.random.org/integers/'
DATA = {'base': 10,
        'format': 'plain',
        'rnd': 'new'}


def dice_roll_random_org(num, sides):
    data = DATA.copy()
    data['num'] = num
    data['col'] = num
    data['min'] = 1
    data['max'] = sides
    res = requests.get(URL, data)
    if res.status_code != 200:
        print(res)
        return -1
    return sum(int(x) for x in res.text.split())


def dice_roll(num, sides):
    result = dice_roll_random_org(num, sides)
    if result == -1:
        # fall back to regular python random
        return sum(random.randint(1, sides) for _ in range(num))
    return result
