from collections.abc import Mapping, Sequence
import json
from curry_quest.floor_descriptor import FloorDescriptor, Monster
from curry_quest.items import all_items
from curry_quest.traits import UnitTraits, Genus, Talents, SpellTraits


class Config:
    class InvalidConfig(Exception):
        pass

    class Timers:
        def __init__(self):
            self.event_interval = 0
            self.event_penalty_duration = 0

    class Probabilities:
        def __init__(self):
            self.flee = 0.0
            self.enemy_spell_attack = 0.0

    class PlayerSelectionWeights:
        def __init__(self):
            self.without_penalty = 0
            self.with_penalty = 0

    class Levels:
        def __init__(self):
            self._experience_per_level = []

        @property
        def max_level(self) -> int:
            return len(self._experience_per_level)

        def add_level(self, experience_required: int):
            self._experience_per_level.append(experience_required)

        def experience_for_next_level(self, level: int) -> int:
            return self._experience_per_level[level]

    class SpecialUnitsTraits:
        def __init__(self):
            self.ghosh = UnitTraits()

    def __init__(self):
        self._channel_id = 0
        self._admin_channel_id = 0
        self._admins = []
        self._timers = self.Timers()
        self._probabilities = self.Probabilities()
        self._player_selection_weights = self.PlayerSelectionWeights()
        self.events_weights = {}
        self.character_events_weights = {}
        self.traps_weights = {}
        self.found_items_weights = {}
        self._levels = self.Levels()
        self._monsters_traits = {}
        self._special_units_traits = self.SpecialUnitsTraits()
        self._floors = []

    @property
    def channel_id(self):
        return self._channel_id

    @property
    def admin_channel_id(self):
        return self._admin_channel_id

    @property
    def admins(self):
        return self._admins

    @property
    def timers(self):
        return self._timers

    @property
    def probabilities(self):
        return self._probabilities

    @property
    def player_selection_weights(self):
        return self._player_selection_weights

    @property
    def levels(self):
        return self._levels

    @property
    def monsters_traits(self) -> Mapping[str, UnitTraits]:
        return self._monsters_traits

    @property
    def special_units_traits(self):
        return self._special_units_traits

    @property
    def floors(self) -> Sequence[FloorDescriptor]:
        return self._floors

    @property
    def highest_floor(self) -> int:
        return len(self._floors)

    @classmethod
    def from_file(cls, config_file) -> '__class__':
        return cls.from_json(config_file.read())

    @classmethod
    def from_json(cls, config_json_string) -> '__class__':
        config = Config()
        try:
            config_json = json.loads(config_json_string)
            config._channel_id = config_json['channel_id']
            config._admin_channel_id = config_json['admin_channel_id']
            config._admins = config_json['admins']
            cls._read_timers(config._timers, config_json['timers'])
            cls._read_probabilities(config._probabilities, config_json['probabilities'])
            cls._read_player_selection_weights(
                config._player_selection_weights,
                config_json['player_selection_weights'])
            config.events_weights = config_json['events_weights']
            config.found_items_weights = config_json['found_items_weights']
            config.character_events_weights = config_json['characters_events_weights']
            config.traps_weights = config_json['traps_weights']
            cls._read_levels(config._levels, config_json['experience_per_level'])
            config._monsters_traits = cls._create_monsters_traits(config_json['monsters'])
            config._special_units_traits = cls._create_special_units_traits(config_json['special_units'])
            config._floors = cls._create_floors(config_json['floors'])
        except json.JSONDecodeError as exc:
            raise cls.InvalidConfig(f"Invalid JSON: {exc}")
        except KeyError as exc:
            raise cls.InvalidConfig(f"Missing key: {exc}")
        cls._validate_config(config)
        return config

    @classmethod
    def _read_timers(cls, timers: '__class__.Timers', timers_json):
        try:
            timers.event_interval = int(timers_json['event_interval'])
            timers.event_penalty_duration = int(timers_json['event_penalty_duration'])
        except ValueError as exc:
            raise cls.InvalidConfig(f"{timers_json}: {exc}")

    @classmethod
    def _read_probabilities(cls, probabilities, probabilities_json):
        try:
            probabilities.flee = float(probabilities_json['flee'])
            probabilities.enemy_spell_attack = float(probabilities_json['enemy_spell_attack'])
        except ValueError as exc:
            raise cls.InvalidConfig(f"{probabilities_json}: {exc}")

    @classmethod
    def _read_player_selection_weights(cls, player_selection_weights, player_selection_weights_json):
        try:
            player_selection_weights.without_penalty = player_selection_weights_json['without_penalty']
            player_selection_weights.with_penalty = player_selection_weights_json['with_penalty']
        except ValueError as exc:
            raise cls.InvalidConfig(f"{player_selection_weights_json}: {exc}")

    @classmethod
    def _read_levels(cls, levels: '__class__.Levels', levels_json):
        experience_for_prev_level = -1
        for level, experience_for_next_level in enumerate(levels_json, start=1):
            if experience_for_next_level <= experience_for_prev_level:
                raise cls.InvalidConfig(f'Experience required for LVL {level} is not greater than for LVL {level - 1}')
            levels.add_level(experience_for_next_level)
            experience_for_prev_level = experience_for_next_level

    @classmethod
    def _create_monsters_traits(cls, monsters_json):
        monsters_traits = {}
        for monster_json in monsters_json:
            monster_traits = cls._create_unit_traits(monster_json)
            if monster_traits.name in monsters_traits:
                raise cls.InvalidConfig(f"Double entry for monster '{monster_traits.name}' traits")
            monsters_traits[monster_traits.name] = monster_traits
        return monsters_traits

    @classmethod
    def _create_unit_traits(cls, unit_json):
        unit_traits = UnitTraits()
        try:
            unit_traits.name = unit_json['name']
            unit_traits.base_hp = unit_json['base_hp']
            unit_traits.hp_growth = unit_json['hp_growth']
            unit_traits.base_mp = unit_json['base_mp']
            unit_traits.mp_growth = unit_json['mp_growth']
            unit_traits.base_attack = unit_json['base_attack']
            unit_traits.attack_growth = unit_json['attack_growth']
            unit_traits.base_defense = unit_json['base_defense']
            unit_traits.defense_growth = unit_json['defense_growth']
            unit_traits.base_luck = unit_json['base_luck']
            unit_traits.luck_growth = unit_json['luck_growth']
            unit_traits.base_exp_given = unit_json['base_exp']
            unit_traits.exp_given_growth = unit_json['exp_growth']
            unit_traits.native_genus = cls._parse_genus(unit_json['element'])
            unit_traits.native_spell_traits = cls._parse_spell(unit_json.get('spell'))
            unit_traits.talents = cls._parse_talents(unit_json.get('talents'))
            unit_traits.is_evolved = unit_json.get('is_evolved', False)
            unit_traits.evolves_into = unit_json.get('evolves_into')
        except KeyError as exc:
            raise cls.InvalidConfig(f"{unit_json}: missing key {exc}")
        except ValueError as exc:
            raise cls.InvalidConfig(f"{unit_json}: {exc}")
        return unit_traits

    @classmethod
    def _parse_genus(cls, genus_name):
        if genus_name == 'None':
            return Genus.Empty
        for genus in Genus:
            if genus.name == genus_name:
                return genus
        raise ValueError(f'Unknown genus "{genus_name}"')

    @classmethod
    def _parse_spell(cls, spell_name):
        if spell_name is None:
            return None
        spell_traits = SpellTraits()
        spell_traits.name = spell_name
        if spell_name == 'Brid':
            spell_traits.base_damage = 10
            spell_traits.genus = Genus.Fire
            spell_traits.mp_cost = 10
        elif spell_name == 'Breath':
            spell_traits.base_damage = 16
            spell_traits.genus = Genus.Fire
            spell_traits.mp_cost = 12
        elif spell_name == 'Sled':
            spell_traits.base_damage = 8
            spell_traits.genus = Genus.Fire
            spell_traits.mp_cost = 8
        elif spell_name == 'Rise':
            spell_traits.base_damage = 19
            spell_traits.genus = Genus.Fire
            spell_traits.mp_cost = 16
        elif spell_name == 'DeHeal':
            spell_traits.base_damage = 10
            spell_traits.genus = Genus.Water
            spell_traits.mp_cost = 10
        else:
            raise ValueError(f'Unknown spell name "{spell_name}"')
        return spell_traits

    @classmethod
    def _parse_talents(cls, talents_string):
        if talents_string is None:
            return Talents.Empty
        talents = Talents.Empty
        for talent_name in talents_string.split(','):
            talents |= cls._parse_talent(talent_name)
        return talents

    @classmethod
    def _parse_talent(cls, talent_name):
        for talent in Talents:
            if talent.name == talent_name:
                return talent
        raise ValueError(f'Unknown talent "{talent_name}"')

    @classmethod
    def _create_special_units_traits(cls, special_units_json):
        special_units_traits = cls.SpecialUnitsTraits()
        try:
            special_units_traits.ghosh = cls._create_unit_traits(special_units_json['ghosh'])
        except KeyError as exc:
            raise cls.InvalidConfig(f'Missing special units traits - {exc}')
        return special_units_traits

    @classmethod
    def _create_floors(cls, floors_json):
        floors = []
        for floor_json in floors_json:
            floors.append(cls._create_floor(floor_json))
        return floors

    @classmethod
    def _create_floor(cls, floor_json):
        floor = FloorDescriptor()
        try:
            for monster_json in floor_json:
                floor.add_monster(
                    Monster(monster_json['monster'], monster_json['level']),
                    monster_json['weight'])
        except KeyError as exc:
            raise cls.InvalidConfig(f"{floor_json}: missing key {exc}")
        return floor

    @classmethod
    def _validate_config(cls, config):
        cls._validate_probabilities(config)
        cls._validate_events_weights(config)
        cls._validate_found_items_weights(config)
        cls._validate_characters_events_weights(config)
        cls._validate_traps_weights(config)
        cls._validate_experience_per_level(config)
        cls._validate_monsters_traits(config)
        cls._validate_floors(config)

    @classmethod
    def _validate_probabilities(cls, config):
        probabilities = config.probabilities
        cls._validate_probability('flee', probabilities.flee)

    @classmethod
    def _validate_probability(cls, name, probability):
        min_probability = 0.0
        max_probability = 1.0
        if probability < min_probability or probability > max_probability:
            raise cls.InvalidConfig(
                f'Probability "{name}"={probability} is outside range [{min_probability}-{max_probability}]')

    @classmethod
    def _validate_events_weights(cls, config):
        cls._validate_weights_dictionary(
            'events_weights',
            config.events_weights,
            ['battle', 'character', 'elevator', 'item', 'trap', 'familiar'])

    @classmethod
    def _validate_found_items_weights(cls, config):
        cls._validate_weights_dictionary(
            'found_items_weights',
            config.found_items_weights,
            [item.name for item in all_items()])

    @classmethod
    def _validate_characters_events_weights(cls, config):
        cls._validate_weights_dictionary(
            'character_events_weights',
            config.character_events_weights,
            ['Cherrl', 'Nico', 'Patty', 'Fur', 'Selfi', 'Mia', 'Vivianne', 'Ghosh', 'Beldo'])

    @classmethod
    def _validate_traps_weights(cls, config):
        cls._validate_weights_dictionary(
            'traps_weights',
            config.traps_weights,
            ['Poison', 'Sleep', 'Upheaval', 'Crack', 'Go up', 'Paralyze', 'Blinder'])

    @classmethod
    def _validate_weights_dictionary(cls, dictionary_name, weights_dictionary, expected_keys):
        missing_keys = set(expected_keys) - set(weights_dictionary.keys())
        if len(missing_keys) > 0:
            missing_keys_string = ', '.join(f'"{missing_key}"' for missing_key in missing_keys)
            raise cls.InvalidConfig(f'"{dictionary_name}" - missing weights for: {missing_keys_string}')
        excessive_keys = set(weights_dictionary.keys()) - set(expected_keys)
        if len(excessive_keys) > 0:
            excessive_keys_string = ', '.join(f'"{excessive_key}"' for excessive_key in excessive_keys)
            raise cls.InvalidConfig(f'"{dictionary_name}" - excessive_keys weights for: {excessive_keys_string}')
        if sum(weights_dictionary.values()) == 0:
            raise cls.InvalidConfig(f'"{dictionary_name}" - all weights are 0s')

    @classmethod
    def _validate_experience_per_level(cls, config):
        if config.levels.max_level == 0:
            raise cls.InvalidConfig(f'No levels defined')

    @classmethod
    def _validate_monsters_traits(cls, config):
        for monster_trait in config.monsters_traits.values():
            if monster_trait.does_evolve() and monster_trait.evolves_into not in config.monsters_traits:
                raise cls.InvalidConfig(
                    f'{monster_trait.name} - unknown monster to evolve to - {monster_trait.evolves_into}')

    @classmethod
    def _validate_floors(cls, config):
        if config.highest_floor == 0:
            raise cls.InvalidConfig(f'No floors specified')
        for index, floor in enumerate(config.floors):
            if len(floor.monsters) == 0:
                raise cls.InvalidConfig(f'Floor at index {index} has no monsters')
            for monster in floor.monsters:
                if monster.name not in config.monsters_traits:
                    raise cls.InvalidConfig(f'Floor at index {index} has unknown monster "{monster.name}"')
