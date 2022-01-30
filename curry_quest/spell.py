from curry_quest.traits import SpellTraits


class Spell:
    def __init__(self, traits: SpellTraits, level=1):
        self._traits = traits
        self.level = level

    @property
    def traits(self) -> SpellTraits:
        return self._traits

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value
