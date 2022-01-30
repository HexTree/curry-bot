class Monster:
    def __init__(self, name: str, level: int):
        self._name = name
        self._level = level

    @property
    def name(self):
        return self._name

    @property
    def level(self):
        return self._level


class FloorDescriptor:
    def __init__(self):
        self._monsters = []
        self._weights = []

    @property
    def monsters(self):
        return self._monsters

    @property
    def weights(self):
        return self._weights

    def add_monster(self, monster: Monster, weight: int):
        self._monsters.append(monster)
        self._weights.append(weight)
