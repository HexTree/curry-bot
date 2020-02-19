import re
import requests
from bs4 import BeautifulSoup

# api-endpoint
URL = "https://bingosync.com/"

DATA = {'nickname':'CurryBot',
        'game_type':18,
        'variant_type':18,
        'lockout_mode':1,
        'seed':1,
        'is_spectator':'on'}


def create_room(name, passphrase, bingo_data):
    # perform GET to obtain csrf
    csrf = requests.get(url=URL).cookies.get('csrftoken')

    cookies = {'csrftoken': csrf}
    data = DATA.copy()
    data['room_name'] = name
    data['csrfmiddlewaretoken'] = csrf
    data['custom_json'] = bingo_data
    data['passphrase'] = passphrase

    # perform POST to create room
    res = requests.post(URL, cookies=cookies, data=data)

    # search for room id in response
    soup = BeautifulSoup(res.text, 'html.parser')
    pattern = r"/room/(.+)/disconnect"
    roomcode = None
    for link in soup.find_all('a'):
        m = re.match(pattern, link.get('href'))
        if m:
            roomcode = m.group(1)
            break
    if roomcode:
        return URL + "room/" + roomcode
