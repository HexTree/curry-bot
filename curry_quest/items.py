from curry_quest.errors import InvalidOperation


def normalize_item_name(*item_name_parts: str):
    item_name = ''.join(item_name_parts)
    return item_name.replace(' ', '').lower()


class Item:
    @classmethod
    @property
    def name(cls) -> str:
        raise NotImplementedError(f'{cls.__name__}.name')

    def can_use(self, context) -> bool:
        raise NotImplementedError(f'{self.__class__.__name__}.{self.can_use}')

    def use(self, context) -> str:
        can_use, reason = self.can_use(context)
        if not can_use:
            raise InvalidOperation(f'Cannot use {self.name}. {reason}')
        effect = self._use(context)
        context.add_response(f"You used the {self.name}. {effect}")

    def _use(self, context) -> str:
        raise NotImplementedError(f"{self.__class__.__name__}.{self.use}")


class Pita(Item):
    @classmethod
    @property
    def name(cls) -> str:
        return 'Pita'

    def can_use(self, context) -> (bool, str):
        if context.familiar.is_mp_at_max():
            return False, 'Your MP is already at max.'
        else:
            return True, ''

    def _use(self, context) -> str:
        context.familiar.restore_mp()
        return 'Your MP has been restored to max.'


class BattlePhaseOnlyItem(Item):
    def can_use(self, context) -> bool:
        if not context.is_in_battle():
            return False, 'You are not in combat.'
        elif context.battle_context.is_prepare_phase():
            return False, 'Combat has not started yet.'
        else:
            return True, ''


class Oleem(BattlePhaseOnlyItem):
    @classmethod
    @property
    def name(cls) -> str:
        return 'Oleem'

    def _use(self, context) -> bool:
        context.battle_context.finish_battle()
        return 'The enemy vanished!'


class HolyScroll(BattlePhaseOnlyItem):
    @classmethod
    @property
    def name(cls) -> str:
        return 'Holy Scroll'

    def _use(self, context) -> str:
        context.battle_context.set_holy_scroll_counter(3)
        return 'You are invulnerable for the next 3 turns.'


class MedicinalHerb(Item):
    @classmethod
    @property
    def name(cls) -> str:
        return 'Medicinal Herb'

    def can_use(self, context) -> bool:
        if context.familiar.is_hp_at_max():
            return False, 'Your HP is already at max.'
        else:
            return True, ''

    def _use(self, context) -> str:
        context.familiar.restore_hp()
        return 'Your HP has been restored to max.'


class CureAllHerb(Item):
    @classmethod
    @property
    def name(cls) -> str:
        return 'Cure-All Herb'

    def can_use(self, context) -> bool:
        if not context.familiar.has_any_status():
            return False, 'You do not have any statuses.'
        else:
            return True, ''

    def _use(self, context) -> str:
        context.familiar.clear_statuses()
        return 'All statuses have been restored.'


class FireBall(BattlePhaseOnlyItem):
    @classmethod
    @property
    def name(cls) -> str:
        return 'Fire Ball'

    def _use(self, context) -> str:
        damage = context.battle_context.enemy.max_hp // 2
        enemy = context.battle_context.enemy
        enemy.deal_damage(damage)
        return f'Flames spew forth from the {self.name} dealing {damage} damage. ' \
            f'{enemy.name} has {enemy.hp} HP left.'


class WaterBall(Item):
    @classmethod
    @property
    def name(cls) -> str:
        return 'Water Ball'

    def can_use(self, context) -> bool:
        familiar = context.familiar
        if familiar.is_hp_at_max() and familiar.is_mp_at_max():
            return False, 'Your HP and MP are already at max.'
        else:
            return True, ''

    def _use(self, context) -> str:
        familiar = context.familiar
        familiar.restore_hp()
        familiar.restore_mp()
        return 'Your HP and MP have been restored to max.'


def all_items():
    return [Pita(), Oleem(), HolyScroll(), MedicinalHerb(), CureAllHerb(), FireBall(), WaterBall()]
