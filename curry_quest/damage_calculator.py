import enum
from curry_quest.unit import Unit


class DamageCalculator:
    class DamageRoll(enum.Enum):
        Low = 0
        Normal = 1
        High = 2

    class RelativeHeight(enum.Enum):
        Lower = -1
        Same = 0
        Higher = 1

        def opposite(self) -> '__class__':
            if self is DamageCalculator.RelativeHeight.Lower:
                return DamageCalculator.RelativeHeight.Higher
            elif self is DamageCalculator.RelativeHeight.Higher:
                return DamageCalculator.RelativeHeight.Lower
            else:
                return DamageCalculator.RelativeHeight.Same

    def __init__(self, attacker: Unit, defender: Unit):
        self._attacker = attacker
        self._defender = defender

    def physical_damage(self, damage_roll: DamageRoll, relative_height: RelativeHeight, is_critical: bool) -> int:
        base_damage = 2 * self._attacker.attack + damage_roll.value
        combat_advantage = self._physical_combat_advantage(relative_height)
        damage_dealt = base_damage + (base_damage * combat_advantage / 8) - self._base_defense()
        damage_dealt = int(damage_dealt / 2 * self._critical_hit_multiplier(is_critical))
        return max(damage_dealt, 1)

    def spell_damage(self) -> int:
        spell = self._attacker.spell
        base_damage = (spell.traits.base_damage + spell.level) * 2
        damage_dealt = int((base_damage + self._spell_combat_damage(base_damage) - self._base_defense()) // 2)
        return max(damage_dealt, 1)

    def _base_defense(self):
        return self._defender.defense

    def _physical_combat_advantage(self, relative_height: RelativeHeight):
        return self._physical_elemental_combat_advantage() + relative_height.value

    def _physical_elemental_combat_advantage(self):
        if self._attacker.genus.is_strong_against(self._defender.genus):
            return 1
        elif self._attacker.genus.is_weak_against(self._defender.genus):
            return -2
        else:
            return 0

    def _spell_combat_damage(self, base_damage):
        combat_advantage = self._spell_combat_advantage()
        combat_damage = base_damage * combat_advantage
        if combat_advantage < 0:
            combat_damage = (combat_damage + 3) / 4
        return combat_damage

    def _spell_combat_advantage(self):
        if self._attacker.genus.is_strong_against(self._defender.genus):
            return 1
        elif self._attacker.genus.is_weak_against(self._defender.genus):
            return -1
        else:
            return 0

    def _critical_hit_multiplier(self, is_critical: bool) -> float:
        return 1.5 if is_critical else 1.0
