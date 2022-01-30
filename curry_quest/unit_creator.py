from curry_quest.config import Config
from curry_quest.stats_calculator import StatsCalculator
from curry_quest.traits import SpellTraits, UnitTraits
from curry_quest.unit import Unit


class UnitCreator:
    def __init__(self, unit_traits: UnitTraits):
        self._unit_traits = unit_traits
        self._spell_traits = None

    def set_spell(self, traits: SpellTraits):
        self._spell_traits = traits
        return self

    def create(self, level, levels: Config.Levels=Config.Levels()) -> Unit:
        stats_calculator = StatsCalculator(self._unit_traits)
        unit = Unit(self._unit_traits, levels)
        unit.level = level
        unit.max_hp = stats_calculator.hp(level)
        unit.hp = unit.max_hp
        unit.max_mp = stats_calculator.mp(level)
        unit.mp = unit.max_mp
        unit.attack = stats_calculator.attack(level)
        unit.defense = stats_calculator.defense(level)
        unit.luck = stats_calculator.luck(level)
        if self._spell_traits is not None:
            unit.set_spell(self, self._spell_traits, level)
        return unit
