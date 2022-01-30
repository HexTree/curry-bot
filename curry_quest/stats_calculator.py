import math
from curry_quest.talents import Talents
from curry_quest.traits import UnitTraits


class StatsCalculator:
    def __init__(self, unit_traits: UnitTraits):
        self._unit_traits = unit_traits

    def hp(self, level):
        return self._evolved_hp(level) if self._is_evolved() else self._non_evolved_hp(level)

    def mp(self, level):
        return self._non_hp_stat(level, self._mp_stat_descriptor())

    def attack(self, level):
        return self._non_hp_stat(level, self._attack_stat_descriptor())

    def defense(self, level):
        return self._non_hp_stat(level, self._defense_stat_descriptor())

    def luck(self, level):
        return self._non_hp_stat(level, self._luck_stat_descriptor())

    def hp_increase(self, level):
        return self._stat_increase(level, self._unit_traits.base_hp, self.hp)

    def mp_increase(self, level):
        return self._stat_increase(level, self._unit_traits.base_mp, self.mp)

    def attack_increase(self, level):
        return self._stat_increase(level, self._unit_traits.base_attack, self.attack)

    def defense_increase(self, level):
        return self._stat_increase(level, self._unit_traits.base_defense, self.defense)

    def luck_increase(self, level):
        return self._stat_increase(level, self._unit_traits.base_luck, self.luck)

    def given_experience(self, level):
        base_exp_given = self._unit_traits.base_exp_given
        exp_growth = self._unit_traits.exp_given_growth
        x = level - 1
        exp = base_exp_given * (x + 1)
        exp += (x * x * (base_exp_given + exp_growth * x)) // 512
        if self._unit_traits.talents.has(Talents.GrowthPromoted):
            exp *= 2
        return min(exp, 65535)

    def _evolved_hp(self, level):
        hp = self._unit_traits.base_hp
        for n in range(2, level + 1):
            hp += self._evolved_hp_increase(n)
        return hp

    def _evolved_hp_increase(self, level):
        if level == 1:
            return self._unit_traits.base_hp
        else:
            hp_growth = self._unit_traits.hp_growth
            hp_increase = hp_growth * (level - 1) // 16
            hp_increase -= hp_growth * (level - 2) // 16
            hp_increase += int(2896 * hp_growth * math.sqrt(hp_growth * (level - 1)) / 32768)
            hp_increase -= int(2896 * hp_growth * math.sqrt(hp_growth * (level - 2)) / 32768)
            return hp_increase

    def _non_evolved_hp(self, level):
        base_hp = self._unit_traits.base_hp
        hp_growth = self._unit_traits.hp_growth
        hp = base_hp
        hp += (hp_growth * (level - 1)) // 16
        hp += int(2896 * hp_growth * math.sqrt(hp_growth * (level - 1)) / 32768)
        return min(hp, 255)

    def _mp_stat_descriptor(self):
        return (self._unit_traits.base_mp, self._unit_traits.mp_growth, 1024)

    def _attack_stat_descriptor(self):
        return (self._unit_traits.base_attack, self._unit_traits.attack_growth, 64)

    def _defense_stat_descriptor(self):
        return (self._unit_traits.base_defense, self._unit_traits.defense_growth, 64)

    def _luck_stat_descriptor(self):
        return (self._unit_traits.base_luck, self._unit_traits.luck_growth, 1024)

    def _non_hp_stat(self, level, stat_descriptor):
        if self._is_evolved():
            return self._evolved_non_hp_stat(level, stat_descriptor)
        else:
            return self._non_evolved_non_hp_stat(level, stat_descriptor)

    def _is_evolved(self) -> bool:
        return self._unit_traits.is_evolved

    def _evolved_non_hp_stat(self, level, stat_descriptor):
        base_stat, _, _ = stat_descriptor
        stat = base_stat
        for n in range(2, level + 1):
            stat += self._evolved_non_hp_stat_increase(n, stat_descriptor)
        return stat

    def _evolved_non_hp_stat_increase(self, level, stat_descriptor):
        base_stat, stat_growth, stat_divisor = stat_descriptor
        if level == 1:
            return base_stat
        else:
            stat_increase = (base_stat * stat_growth * (level - 1)) // stat_divisor
            stat_decrease = (base_stat * stat_growth * (level - 2)) // stat_divisor
            return stat_increase - stat_decrease

    def _non_evolved_non_hp_stat(self, level, stat_descriptor):
        base_stat, stat_growth, stat_divisor = stat_descriptor
        return min(base_stat + (base_stat * stat_growth * (level - 1) // stat_divisor), 255)

    def _stat_increase(self, level, base_stat, calculate_stat):
        if level == 1:
            return base_stat
        else:
            stat_at_level = calculate_stat(level)
            stat_at_prev_level = calculate_stat(level - 1)
            return stat_at_level - stat_at_prev_level
