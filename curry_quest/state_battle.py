from curry_quest import commands
from curry_quest.damage_calculator import DamageCalculator
from curry_quest.items import Item
from curry_quest.state_base import StateBase
from curry_quest.state_with_inventory_item import StateWithInventoryItem
from curry_quest.stats_calculator import StatsCalculator
from curry_quest.state_machine_context import BattleContext
from curry_quest.statuses import Statuses
from curry_quest.talents import Talents
from curry_quest.unit import Unit
from curry_quest.unit_creator import UnitCreator

DamageRoll = DamageCalculator.DamageRoll
RelativeHeight = DamageCalculator.RelativeHeight


class StateBattleEvent(StateBase):
    def __init__(self, context, monster_traits: dict=None, monster_level: int=0):
        super().__init__(context)
        self._monster_traits = monster_traits
        self._monster_level = monster_level

    def on_enter(self):
        self._context.generate_action(commands.START_BATTLE, self._select_enemy())

    def _select_enemy(self):
        if self._monster_traits is None:
            return self._context.generate_floor_monster(floor=self._context.floor)
        else:
            monster_level = self._monster_level if self._monster_level > 0 else self._context.familiar.level
            return UnitCreator(self._monster_traits).create(monster_level)

    @classmethod
    def _parse_args(cls, context, args):
        if len(args) == 0:
            return ()
        monster_name = args[0]
        if monster_name not in context.game_config.monsters_traits.keys():
            raise cls.ArgsParseError('Unknown monster')
        monster_traits = context.game_config.monsters_traits[monster_name]
        monster_level = 0
        if len(args) > 1:
            try:
                monster_level = int(args[1])
            except ValueError:
                raise cls.ArgsParseError('Monster level is not a number')
        return monster_traits, monster_level


class StateBattleBase(StateBase):
    @property
    def _battle_context(self) -> BattleContext:
        return self._context.battle_context


class StateStartBattle(StateBattleBase):
    def __init__(self, context, enemy: Unit):
        super().__init__(context)
        self._enemy = enemy

    def on_enter(self):
        enemy = self._enemy
        self._context.add_response(f"You encountered a LVL {enemy.level} {enemy.name} ({enemy.hp} HP).")
        self._context.add_response(f"{enemy.to_string()}.")
        self._context.start_battle(self._enemy)
        self._battle_context.start_prepare_phase(counter=3)
        self._context.generate_action(commands.BATTLE_PREPARE_PHASE, (True,))

    @classmethod
    def _parse_args(cls, context, args):
        return args[0],


class StateBattlePreparePhase(StateBattleBase):
    def __init__(self, context, prepare_phase_turn_used: bool):
        super().__init__(context)
        self._prepare_phase_turn_used = prepare_phase_turn_used

    def on_enter(self):
        if self._context.familiar.has_status(Statuses.Sleep):
            self._context.add_response(
                "You are very sleepy. As you're nodding off, an enemy approaches you. Time to battle!")
            self._battle_context.finish_prepare_phase()
        else:
            if self._prepare_phase_turn_used:
                self._battle_context.dec_prepare_phase_counter()
            if not self._battle_context.is_prepare_phase():
                self._context.add_response("The enemy approaches you. Time to battle!")
            elif self._prepare_phase_turn_used:
                self._context.add_response("The enemy is close, but you still have time to prepare.")
        if not self._battle_context.is_prepare_phase():
            self._context.generate_action(commands.BATTLE_PREPARE_PHASE_FINISHED)

    def is_waiting_for_user_action(self) -> bool:
        return True

    @classmethod
    def _parse_args(cls, context, args):
        return args[0],


class StateBattleApproach(StateBattleBase):
    def on_enter(self):
        self._battle_context.finish_prepare_phase()
        self._context.add_response("Time to battle!")
        self._context.generate_action(commands.BATTLE_PREPARE_PHASE_FINISHED)


class StateBattlePhaseBase(StateBattleBase):
    def _is_enemy_dead(self) -> bool:
        return self._battle_context.enemy.is_dead()

    def _is_familiar_dead(self) -> bool:
        return self._context.familiar.is_dead()

    def _is_battle_finished(self) -> bool:
        return self._battle_context.is_finished() or self._is_enemy_dead() or self._is_familiar_dead()

    def _perform_physical_attack(self, attacker: Unit, defender: Unit):
        if not self._is_physical_attack_accurate(attacker):
            return self._physical_attack_miss_response(attacker, defender)
        else:
            damage_calculator = DamageCalculator(attacker, defender)
            relative_height = self._select_relative_height(attacker, defender)
            is_critical = self._select_whether_attack_is_critical(attacker)
            damage = damage_calculator.physical_damage(self._select_damage_roll(), relative_height, is_critical)
            defender.deal_damage(damage)
            physical_attack_descriptor = damage, relative_height, is_critical
            response = self._physical_attack_hit_response(attacker, defender, physical_attack_descriptor)
            if defender.talents.has(Talents.ElectricShock):
                shock_damage = max(damage // 4, 1)
                attacker.deal_damage(shock_damage)
                response += ' ' + self._shock_damage_response(attacker, defender, shock_damage)
            return response

    def _perform_spell_attack(self, attacker: Unit, defender: Unit):
        damage = DamageCalculator(attacker, defender).spell_damage()
        defender.deal_damage(damage)
        attacker.use_mp(attacker.spell.traits.mp_cost)
        return self._spell_attack_response(attacker, defender, damage)

    def _is_physical_attack_accurate(self, attacker: Unit):
        if attacker.luck <= 0:
            return False
        else:
            hit_chance = (attacker.luck - 1) / attacker.luck
            if attacker.has_status(Statuses.Blind):
                hit_chance /= 2
            return self._context.does_action_succeed(success_chance=hit_chance)

    def _select_damage_roll(self) -> DamageRoll:
        return self._context.rng.choices([DamageRoll.Low, DamageRoll.Normal, DamageRoll.High], weights=[1, 2, 1])[0]

    def _select_relative_height(self, attacker: Unit, defender: Unit) -> RelativeHeight:
        def unit_height(unit: Unit):
            unit_height = 0
            if unit.has_status(Statuses.Crack):
                unit_height -= 1
            if unit.has_status(Statuses.Upheavel):
                unit_height += 1
            return unit_height

        attacker_height = unit_height(attacker)
        defender_height = unit_height(defender)
        relative_height = attacker_height - defender_height
        if relative_height > 0:
            return RelativeHeight.Higher
        elif relative_height < 0:
            return RelativeHeight.Lower
        else:
            return RelativeHeight.Same

    def _select_whether_attack_is_critical(self, attacker: Unit) -> bool:
        divider = 2 if attacker.talents.has(Talents.Atrocious) else 64
        crit_chance = (attacker.luck // divider + 1) / 128
        return self._context.does_action_succeed(success_chance=crit_chance)

    def _physical_attack_miss_response(self, attacker: Unit, defender: Unit):
        def is_familiar_attack() -> bool:
            return attacker is self._context.familiar

        response = 'You try' if is_familiar_attack() else f'{attacker.name} tries'
        response += ' to hit '
        response += f'{defender.name}' if is_familiar_attack() else 'you'
        response += ', but '
        response += 'it' if is_familiar_attack() else f'you'
        response += ' dodge'
        if is_familiar_attack():
            response += 's'
        response += ' swiftly.'
        return response

    def _physical_attack_hit_response(self, attacker: Unit, defender: Unit, physical_attack_descriptor):
        def is_familiar_attack() -> bool:
            return attacker is self._context.familiar

        def attacker_name() -> str:
            return 'you' if is_familiar_attack() else attacker.name

        def defender_name() -> str:
            return defender.name if is_familiar_attack() else 'you'

        damage, relative_height, is_critical = physical_attack_descriptor
        response = f'{attacker_name().capitalize()} hit'
        if not is_familiar_attack():
            response += 's'
        response += ' '
        if is_critical:
            response += 'hard '
        if relative_height is RelativeHeight.Higher:
            response += 'from above '
        elif relative_height is RelativeHeight.Lower:
            response += 'from below '
        response += f'dealing {damage} damage. {defender_name().capitalize()} '
        response += 'has' if is_familiar_attack() else 'have'
        response += f' {defender.hp} HP left.'
        return response

    def _shock_damage_response(self, attacker: Unit, defender: Unit, shock_damage: int):
        def is_familiar_attack() -> bool:
            return attacker is self._context.familiar

        response = 'An electrical shock runs through '
        response += 'your' if is_familiar_attack() else f'{attacker.name}\'s'
        response += f' body dealing {shock_damage} damage. '
        response += 'You have' if is_familiar_attack() else f'{attacker.name} has'
        response += f' {attacker.hp} HP left.'
        return response

    def _spell_attack_response(self, attacker: Unit, defender: Unit, damage: int):
        def is_familiar_attack() -> bool:
            return attacker is self._context.familiar

        def attacker_name() -> str:
            return 'you' if is_familiar_attack() else attacker.name

        def defender_name() -> str:
            return defender.name if is_familiar_attack() else 'you'

        response = f'{attacker_name().capitalize()} cast'
        if not is_familiar_attack():
            response += 's'
        response += f' {attacker.spell.traits.name} '
        response += f'dealing {damage} damage. {defender_name().capitalize()} '
        response += 'has' if is_familiar_attack() else 'have'
        response += f' {defender.hp} HP left.'
        return response


class StateBattlePhase(StateBattlePhaseBase):
    def on_enter(self):
        if self._is_battle_finished():
            self._clear_statuses()
            if self._is_enemy_dead():
                self._handle_enemy_defeated()
            self._context.finish_battle()
            if self._is_familiar_dead():
                self._context.add_response("You died...")
                self._context.generate_action(commands.YOU_DIED)
            else:
                self._context.generate_action(commands.EVENT_FINISHED)
        else:
            next_one_to_act_changed = self._select_next_one_to_act()
            self._handle_counters(next_one_to_act_changed)
            if self._battle_context.is_player_turn:
                self._context.generate_action(commands.PLAYER_TURN)
            else:
                self._context.generate_action(commands.ENEMY_TURN)

    def _clear_statuses(self):
        familiar = self._context.familiar
        if familiar.has_any_status():
            familiar.clear_statuses()
            self._context.add_response(f"All statuses have been cleared.")

    def _handle_enemy_defeated(self):
        enemy = self._battle_context.enemy
        response = f'You defeated the {enemy.name}'
        familiar = self._context.familiar
        if not familiar.is_max_level():
            gained_exp = self._calculate_gained_exp()
            response += f' and gained {gained_exp} EXP.'
            has_leveled_up = familiar.gain_exp(gained_exp)
            if has_leveled_up:
                response += f' You leveled up! Your new stats - {familiar.stats_to_string()}.'
        else:
            response += '.'
        self._context.add_response(response)

    def _calculate_gained_exp(self):
        enemy = self._battle_context.enemy
        given_experience = StatsCalculator(enemy.traits).given_experience(enemy.level)
        if enemy.level > self._context.familiar.level:
            given_experience *= 2
        return given_experience

    def _select_next_one_to_act(self):
        if self._battle_context.is_first_turn:
            self._battle_context.is_first_turn = False
            return False
        if self._battle_context.is_player_turn:
            attacker = self._context.familiar
            defender = self._battle_context.enemy
        else:
            attacker = self._battle_context.enemy
            defender = self._context.familiar
        if attacker.talents.has(Talents.Quick) and not defender.talents.has(Talents.Quick):
            max_turn_counter = 2
        else:
            max_turn_counter = 1
        self._battle_context.inc_turn_counter()
        if self._battle_context.turn_counter >= max_turn_counter:
            self._battle_context.is_player_turn = not self._battle_context.is_player_turn
            self._battle_context.clear_turn_counter()
            return True
        else:
            return False

    def _handle_counters(self, next_one_to_act_changed):
        if not next_one_to_act_changed:
            return
        if not self._battle_context.is_holy_scroll_active():
            return
        if self._battle_context.is_player_turn:
            self._battle_context.dec_holy_scroll_counter()
        if not self._battle_context.is_holy_scroll_active():
            self._context.add_response("The Holy Scroll's beams dissipate.")


class StateBattlePlayerTurn(StateBattlePhaseBase):
    def on_enter(self):
        self._context.add_response(f"Your turn.")

    def is_waiting_for_user_action(self) -> bool:
        return True


class StateEnemyStats(StateBattleBase):
    def on_enter(self):
        self._context.add_response(f"Enemy stats: {self._battle_context.enemy.to_string()}.")
        self._context.generate_action(commands.PLAYER_TURN)


class StateBattleAttack(StateBattlePhaseBase):
    def on_enter(self):
        familiar = self._context.familiar
        enemy = self._battle_context.enemy
        response = self._perform_physical_attack(attacker=familiar, defender=enemy)
        self._context.add_response(response)
        self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)


class StateBattleUseSpell(StateBattlePhaseBase):
    def on_enter(self):
        familiar = self._context.familiar
        if not familiar.has_spell():
            self._context.add_response("You do not have a spell.")
            self._context.generate_action(commands.CANNOT_USE_SPELL)
        elif not familiar.has_enough_mp_for_spell():
            self._context.add_response("You do not have enough MP.")
            self._context.generate_action(commands.CANNOT_USE_SPELL)
        else:
            response = self._perform_spell_attack(attacker=familiar, defender=self._battle_context.enemy)
            self._context.add_response(response)
            self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)

    @classmethod
    def _verify_preconditions(cls, context, parsed_args):
        familiar = context.familiar
        if not familiar.has_spell():
            raise cls.PreConditionsNotMet('You do not have a spell.')
        if not familiar.has_enough_mp_for_spell():
            raise cls.PreConditionsNotMet('You do not have enough MP.')


class StateBattleUseItem(StateWithInventoryItem):
    @property
    def _battle_context(self) -> BattleContext:
        return self._context.battle_context

    def on_enter(self):
        item = self._context.inventory.peek_item(self._item_index)
        can_use, reason = item.can_use(self._context)
        if not can_use:
            command, args = self._handle_cannot_use_item(item, reason)
        else:
            command, args = self._handle_can_use_item(item)
        self._context.generate_action(command, *args)

    def _handle_cannot_use_item(self, item: Item, reason: str):
        self._context.add_response(f"You cannot use {item.name}. {reason}")
        if self._battle_context.is_prepare_phase():
            return commands.CANNOT_USE_ITEM_PREPARE_PHASE, (False, )
        else:
            return commands.CANNOT_USE_ITEM_BATTLE_PHASE, ()

    def _handle_can_use_item(self, item: Item):
        item.use(self._context)
        self._context.inventory.take_item(self._item_index)
        if self._battle_context.is_prepare_phase():
            return commands.BATTLE_PREPARE_PHASE_ACTION_PERFORMED, (True, )
        else:
            return commands.BATTLE_ACTION_PERFORMED, ()


class StateBattleTryToFlee(StateBattlePhaseBase):
    def on_enter(self):
        if self._context.familiar.has_status(Statuses.Paralyze):
            self._context.add_response("You are paralyzed and cannot flee.")
            self._context.generate_action(commands.CANNOT_FLEE)
            return
        if self._context.does_action_succeed(success_chance=self.game_config.probabilities.flee):
            self._battle_context.finish_battle()
            self._context.add_response("You successfully flee from the battle.")
        else:
            self._context.add_response("You attempt to flee from battle, but your path is blocked!")
        self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)


class StateBattleEnemyTurn(StateBattlePhaseBase):
    def on_enter(self):
        enemy = self._battle_context.enemy
        if self._battle_context.is_holy_scroll_active():
            self._context.add_response(f"The field is engulfed in the Holy Scroll's beams. {enemy.name} cannot act.")
        else:
            familiar = self._context.familiar
            enemy = self._battle_context.enemy
            perform_spell_attack = False
            if enemy.has_spell() and enemy.has_enough_mp_for_spell():
                perform_spell_attack = self._context.does_action_succeed(
                    self.game_config.probabilities.enemy_spell_attack)
            if perform_spell_attack:
                response = self._perform_spell_attack(attacker=enemy, defender=familiar)
            else:
                response = self._perform_physical_attack(attacker=enemy, defender=familiar)
            self._context.add_response(response)
        self._context.generate_action(commands.BATTLE_ACTION_PERFORMED)
