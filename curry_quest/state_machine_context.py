import copy
import jsonpickle
import random
from curry_quest.config import Config
from curry_quest.errors import InvalidOperation
from curry_quest.inventory import Inventory
from curry_quest.unit import Unit
from curry_quest.state_machine_action import StateMachineAction
from curry_quest.talents import Talents
from curry_quest.traits import UnitTraits
from curry_quest.unit_creator import UnitCreator
from curry_quest.items import Item


class BattleContext:
    def __init__(self, enemy: Unit):
        self._enemy = enemy
        self._prepare_phase_counter = 0
        self._holy_scroll_counter = 0
        self.is_first_turn = True
        self.is_player_turn = True
        self.clear_turn_counter()
        self._finished = False

    @property
    def enemy(self) -> Unit:
        return self._enemy

    def start_prepare_phase(self, counter: int):
        self._prepare_phase_counter = counter

    def is_prepare_phase(self) -> bool:
        return self._prepare_phase_counter > 0

    def dec_prepare_phase_counter(self):
        self._prepare_phase_counter -= 1

    def finish_prepare_phase(self):
        self._prepare_phase_counter = 0

    def is_holy_scroll_active(self) -> bool:
        return self._holy_scroll_counter > 0

    def dec_holy_scroll_counter(self):
        self._holy_scroll_counter -= 1

    def set_holy_scroll_counter(self, counter):
        self._holy_scroll_counter = counter

    @property
    def turn_counter(self):
        return self._turn_counter

    def inc_turn_counter(self):
        self._turn_counter += 1

    def clear_turn_counter(self):
        self._turn_counter = 0

    def is_finished(self):
        return self._finished

    def finish_battle(self):
        self._finished = True


class StateMachineContext:
    RESPONSE_LINE_BREAK = '\n'

    def __init__(self, game_config: Config):
        self._game_config = game_config
        self._is_tutorial_done = False
        self._floor = 0
        self._familiar = None
        self._inventory = Inventory()
        self._battle_context = None
        self._item_buffer = None
        self._unit_buffer = None
        self._rng = random.Random()
        self._responses = []
        self._generated_action = None

    def to_json(self):
        context_copy = copy.deepcopy(self)
        del context_copy._game_config
        return jsonpickle.encode(context_copy)

    @classmethod
    def from_json(cls, context_json, game_config):
        context = jsonpickle.decode(context_json)
        context._game_config = game_config
        return context

    @property
    def game_config(self):
        return self._game_config

    @property
    def is_tutorial_done(self) -> bool:
        return self._is_tutorial_done

    def set_tutorial_done(self):
        self._is_tutorial_done = True

    @property
    def floor(self):
        return self._floor

    @floor.setter
    def floor(self, value):
        self._floor = value

    @property
    def familiar(self) -> Unit:
        return self._familiar

    @familiar.setter
    def familiar(self, value):
        self._familiar = value

    @property
    def inventory(self) -> Inventory:
        return self._inventory

    @property
    def battle_context(self) -> BattleContext:
        return self._battle_context

    def clear_item_buffer(self):
        self._item_buffer = None

    def buffer_item(self, item: Item):
        if self._item_buffer is not None:
            raise InvalidOperation(f'Item already buffered - {self._item_buffer.name}')
        self._item_buffer = item

    def peek_buffered_item(self) -> Item:
        return self._item_buffer

    def take_buffered_item(self) -> Item:
        item = self.peek_buffered_item()
        self.clear_item_buffer()
        return item

    def clear_unit_buffer(self):
        self._unit_buffer = None

    def buffer_unit(self, unit: Unit):
        self._unit_buffer = unit

    def peek_buffered_unit(self) -> Unit:
        return self._unit_buffer

    def take_buffered_unit(self) -> Unit:
        unit = self.peek_buffered_unit()
        self.clear_unit_buffer()
        return unit

    @property
    def rng(self):
        return self._rng

    def does_action_succeed(self, success_chance: float):
        return self.rng.random() < success_chance

    def is_in_battle(self) -> bool:
        return self._battle_context is not None

    def clear_battle_context(self):
        self._battle_context = None

    def start_battle(self, enemy: Unit):
        if self.is_in_battle():
            raise InvalidOperation(f'Battle already started - {enemy.name}')
        self._battle_context = BattleContext(enemy)

    def finish_battle(self):
        if not self.is_in_battle():
            raise InvalidOperation(f'Battle not started')
        self.clear_battle_context()

    def generate_floor_monster(self, floor: int, level_increase: int=0) -> Unit:
        highest_floor = self.game_config.highest_floor
        if floor > highest_floor:
            raise InvalidOperation(f'Highest floor is {highest_floor}')
        floor_descriptor = self.game_config.floors[floor]
        monster_descriptor = self.random_selection_with_weights(
            dict(zip(floor_descriptor.monsters, floor_descriptor.weights)))
        monster_traits = self.game_config.monsters_traits[monster_descriptor.name].copy()
        self._remove_enemy_forbidden_talents(monster_traits)
        monster_level = min(monster_descriptor.level + level_increase, self.game_config.levels.max_level)
        return UnitCreator(monster_traits).create(monster_level)

    def random_selection_with_weights(self, element_weight_dictionary: dict):
        return self.rng.choices(list(element_weight_dictionary.keys()), list(element_weight_dictionary.values()))[0]

    def _remove_enemy_forbidden_talents(self, enemy_traits: UnitTraits):
        enemy_traits.talents &= ~(Talents.StrengthIncreased | Talents.Hard)

    def generate_action(self, command, *args):
        if self._generated_action is not None:
            raise InvalidOperation(f'Already generated - {self._generated_action}')
        self._generated_action = StateMachineAction(command, args, is_given_by_admin=True)

    def has_action(self) -> bool:
        return self._generated_action is not None

    def take_action(self) -> StateMachineAction:
        action = self._generated_action
        self._generated_action = None
        return action

    def add_response(self, response: str):
        self._responses.append(response)

    def add_response_line_break(self):
        self._responses.append(self.RESPONSE_LINE_BREAK)

    def peek_responses(self) -> list:
        return self._responses[:]

    def take_responses(self) -> list:
        responses = self.peek_responses()
        self._responses.clear()
        return responses
