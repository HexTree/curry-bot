import logging
from curry_quest.config import Config
from curry_quest.errors import InvalidOperation
from curry_quest.genus import Genus
from curry_quest.spell import Spell
from curry_quest.talents import Talents
from curry_quest.traits import SpellTraits, UnitTraits
from curry_quest.stats_calculator import StatsCalculator
from curry_quest.statuses import Statuses

logger = logging.getLogger(__name__)


class Unit:
    def __init__(self, traits: UnitTraits, levels: Config.Levels):
        self._traits = traits
        self._levels = levels
        self.name = traits.name
        self.genus = traits.native_genus
        self.level = 1
        self._talents = traits.talents
        self.max_hp = traits.base_hp
        self.hp = self.max_hp
        self.max_mp = traits.base_mp
        self.mp = self.max_mp
        self.attack = traits.base_attack
        self.defense = traits.base_defense
        self.luck = traits.base_luck
        self.clear_statuses()
        if traits.native_spell_traits is not None:
            self.set_spell(traits.native_spell_traits, self.level)
        else:
            self.clear_spell()
        self.exp = 0

    @property
    def traits(self):
        return self._traits

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def genus(self) -> Genus:
        return self._genus

    @genus.setter
    def genus(self, value: Genus):
        self._genus = value

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value

    def is_max_level(self) -> bool:
        return self.level >= self._levels.max_level

    @property
    def talents(self) -> Talents:
        return self._talents

    @property
    def max_hp(self):
        multiplier = 2 if self.talents.has(Talents.HpIncreased) else 1
        return self._max_hp * multiplier

    @max_hp.setter
    def max_hp(self, value):
        self._max_hp = value

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = value

    def is_hp_at_max(self) -> bool:
        return self.hp >= self.max_hp

    def is_dead(self) -> bool:
        return self.hp <= 0

    def restore_hp(self):
        self.hp = self.max_hp

    def deal_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

    @property
    def max_mp(self):
        multiplier = 2 if self.talents.has(Talents.MpIncreased) else 1
        return self._max_mp * multiplier

    @max_mp.setter
    def max_mp(self, value):
        self._max_mp = value

    @property
    def mp(self):
        return self._mp

    @mp.setter
    def mp(self, value):
        self._mp = value

    def is_mp_at_max(self) -> bool:
        return self.mp >= self.max_mp

    def restore_mp(self):
        self.mp = self.max_mp

    def use_mp(self, mp_usage):
        if self.talents.has(Talents.MpConsumptionDecreased):
            mp_usage -= mp_usage // 2
        self.mp -= mp_usage
        if self.mp < 0:
            self.mp = 0

    @property
    def attack(self):
        multiplier = 2 if self.talents.has(Talents.StrengthIncreased) else 1
        return int(self._attack * self._stat_factor() * multiplier)

    @attack.setter
    def attack(self, value):
        self._attack = value

    @property
    def defense(self):
        multiplier = 2 if self.talents.has(Talents.Hard) else 1
        return int(self._defense * self._stat_factor() * multiplier)

    @defense.setter
    def defense(self, value):
        self._defense = value

    @property
    def luck(self):
        return int(self._luck * self._stat_factor())

    @luck.setter
    def luck(self, value):
        self._luck = value

    def _stat_factor(self) -> float:
        STAT_BOOST_FACTOR = 0.5
        stat_factor = 1.0
        if self.has_boosted_stats():
            stat_factor += STAT_BOOST_FACTOR
        return stat_factor

    def has_any_status(self) -> bool:
        return self._statuses.value != 0

    def has_status(self, status: Statuses) -> bool:
        return (self._statuses & status) == status

    def has_boosted_stats(self) -> bool:
        return self.has_status(Statuses.StatsBoost)

    def set_status(self, status: Statuses):
        self._statuses |= status

    def clear_statuses(self):
        self._statuses = Statuses(0)

    def clear_status(self, status: Statuses):
        self._statuses &= ~status

    @property
    def spell(self) -> Spell:
        if not self.has_spell():
            return None
        spell_level = self._spell_level
        if self.talents.has(Talents.MagicAttackIncreased):
            spell_level *= 2
        return Spell(self._spell_traits, spell_level)

    def has_spell(self) -> bool:
        return self._spell_traits is not None

    def set_spell(self, traits: SpellTraits, level: int):
        self._spell_traits = traits
        self._spell_level = level

    def clear_spell(self):
        self._spell_traits = None
        self._spell_level = 0

    @property
    def spell_mp_cost(self) -> int:
        return self._spell_traits.mp_cost

    def has_enough_mp_for_spell(self) -> bool:
        return self.mp >= self.spell_mp_cost

    @property
    def exp(self):
        return self._exp

    @exp.setter
    def exp(self, value):
        self._exp = value

    def gain_exp(self, gained_exp) -> bool:
        has_leveled_up = False
        if self.is_max_level():
            return has_leveled_up
        self.exp += gained_exp
        while not self.is_max_level() and self.exp >= self.experience_for_next_level():
            has_leveled_up = True
            self._level_up()
        return has_leveled_up

    def experience_for_next_level(self) -> int:
        if self.is_max_level():
            return 0
        return self._levels.experience_for_next_level(self.level)

    def fuse(self, other: '__class__'):
        self._talents = self.traits.talents | other.traits.talents
        if self.genus.is_weak_against(other.genus):
            self._genus = other.genus

    def does_evolve(self) -> bool:
        return self.traits.does_evolve()

    def evolve(self, evolved_unit_traits: UnitTraits):
        if not self.does_evolve():
            raise InvalidOperation(f'{self.name} does not evolve.')
        self._traits = evolved_unit_traits
        self.name = evolved_unit_traits.name

    def _level_up(self):
        are_stats_boosted = self.has_boosted_stats()
        if are_stats_boosted:
            self.clear_status(Statuses.StatsBoost)
        self.level += 1
        self._increase_hp_on_level_up()
        self._increase_mp_on_level_up()
        self._increase_attack_on_level_up()
        self._increase_defense_on_level_up()
        self._increase_luck_on_level_up()
        self._increase_spell_level_on_level_up()
        if are_stats_boosted:
            self.set_status(Statuses.StatsBoost)

    def _increase_hp_on_level_up(self):
        hp_increase = self._stats_calculator().hp_increase(self.level)
        self._max_hp += hp_increase
        self._hp += hp_increase

    def _increase_mp_on_level_up(self):
        mp_increase = self._stats_calculator().mp_increase(self.level)
        self._max_mp += mp_increase
        self._mp += mp_increase

    def _increase_attack_on_level_up(self):
        self._attack += self._stats_calculator().attack_increase(self.level)

    def _increase_defense_on_level_up(self):
        self._defense += self._stats_calculator().defense_increase(self.level)

    def _increase_luck_on_level_up(self):
        self._luck += self._stats_calculator().luck_increase(self.level)

    def _increase_spell_level_on_level_up(self):
        if not self.has_spell():
            return
        if self._spell_traits.genus != self.genus:
            return
        self._spell_level += 1
        if self._spell_level < self.level:
            self._spell_level += 1

    def _stats_calculator(self) -> StatsCalculator:
        return StatsCalculator(self.traits)

    def to_string(self) -> str:
        return f'{self.name} - {self.stats_to_string()}'

    def stats_to_string(self) -> str:
        s = f'genus: {self._genus_to_string()}, talents: {self._talents_to_string()}, LVL: {self.level}, ' \
            f'HP: {self.hp}/{self.max_hp}, MP: {self.mp}/{self.max_mp}, ' \
            f'ATK: {self.attack}, DEF: {self.defense}, LUCK: {self.luck}'
        if self.has_any_status():
            s += f', statuses: {self._statuses_to_string()}'
        if self.has_spell():
            s += f', spell: LVL {self.spell.level} {self.spell.traits.name} (MP cost: {self.spell_mp_cost})'
        s += f', EXP: {self.exp}'
        if not self.is_max_level():
            s += f' ({self.experience_for_next_level() - self.exp} more EXP to next LVL)'
        return s

    def _genus_to_string(self) -> str:
        if self.genus is Genus.Empty:
            return '-'
        else:
            return self.genus.name

    def _talents_to_string(self) -> str:
        if self.talents is Talents.Empty:
            return '-'
        else:
            return ', '.join(talent.name for talent in Talents.all() if self.talents.has(talent))

    def _statuses_to_string(self) -> str:
        return ', '.join(status.name for status in Statuses if self.has_status(status))
