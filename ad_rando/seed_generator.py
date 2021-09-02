import hashlib
import math
import struct
import time


class CurryError(BaseException):
    def __init__(self, error_message):
        self.error_message = error_message


class SeedGenerator:
    def __init__(self, validator):
        self._validator = validator
        self._seed_base = time.time() * 1000
        self._seed_floor = math.floor(self._seed_base)
        # Use the nanosecond portion of the time as a pseudo-random offset, plus a constant in case that happens to be 0
        self._offset = math.floor((self._seed_base - self._seed_floor) * 1000) + 50
        self._index = 0

    def next(self):
        seed = self._generate()
        while not self._validator.validate(seed):
            seed = self._generate()
        return seed

    def _generate(self):
        seed = self._seed_floor - self._offset * self._index
        self._index += 1
        return seed


class SeedsGenerator:
    RANDO_BASE = 'https://adrando.com/'

    def __init__(self, randomizer_params, validator, seeds_number):
        self._randomizer_params = randomizer_params
        self._validator = validator
        self._seeds_number = seeds_number

    def generate(self):
        seed_generator = SeedGenerator(self._validator)
        return [self._create_adrando_link(seed_generator.next()) for _ in range(self._seeds_number)]

    def _create_adrando_link(self, seed):
        return f"{self.RANDO_BASE}?{self._randomizer_params.params()},,{seed}"


class AdRandomizerParams:
    def params(self):
        raise NotImplementedError(f'{self.__class__.__name__}.{self.params}')


class FromPresetRandomizerParams(AdRandomizerParams):
    def __init__(self, preset_name):
        self._preset_name = preset_name

    def params(self):
        return f'P:{self._preset_name}'


class ManualRandomizerParams(AdRandomizerParams):
    def __init__(self, params_string):
        self._params_string = params_string

    def params(self):
        return self._params_string


class SeedValidator:
    def validate(self, seed):
        raise NotImplementedError(f'{self.__class__.__name__}.{self.validate}')


class NoRestrictionsSeedValidator(SeedValidator):
    def validate(self, seed):
        return True


class NoHiKewneSeedValidator(SeedValidator):
    STARTER_MONSTER_HASH_HEX_INDEX = 6
    MONSTERS_NUMBER = 45
    HIKEWNE_MONSTER_ID = 1

    def validate(self, seed):
        return self._calculate_starter_monster_id(self._calculate_sha256(seed)) != self.HIKEWNE_MONSTER_ID

    def _calculate_sha256(self, seed):
        m = hashlib.sha256()
        m.update(str.encode(str(seed)))
        return m.digest()

    def _calculate_starter_monster_id(self, seed_hash):
        return (1 + self._calculate_used_hash_hex(seed_hash) % self.MONSTERS_NUMBER)

    def _calculate_used_hash_hex(self, seed_hash):
        seed_hash_start_byte = self.STARTER_MONSTER_HASH_HEX_INDEX * 4
        seed_hash_end_byte = seed_hash_start_byte + 4
        return int(math.fabs(struct.unpack('!i', seed_hash[seed_hash_start_byte:seed_hash_end_byte])[0]))


class AdRandomizerParamsDescriptorSelector:
    ADRANDO_PRESETS = {
        'secondTower': 'Only Second Tower',
        'secondTowerRun': 'Speedrun Second Tower',
        'starsTournament': 'STARS Tournament',
        'tournament': 'RM3T #2 Tournament'
    }
    MANUAL_PRESETS = {
        'randomToolkit': (
            'RM3T #3 Random Toolkit Tournament',
            ManualRandomizerParams('dE:-2,fh:1,iInS:0,txX'),
            NoHiKewneSeedValidator()
        ),
        'sde': (
            'RM3T #5 Random Toolkit Tournament 2: State Display Edition',
            ManualRandomizerParams('BdDE:-2,fh:1,iIlnS:0,txX'),
            NoHiKewneSeedValidator()
        )
    }

    @classmethod
    def select(cls, searched_preset_name):
        def matches_preset(preset):
            preset_name, _ = preset
            return preset_name.startswith(searched_preset_name)

        def matches_preset_exactly(preset):
            preset_name, _ = preset
            return preset_name == searched_preset_name

        matching_presets = list(filter(matches_preset, cls.all_presets().items()))
        if len(matching_presets) > 1:
            matching_presets = list(filter(matches_preset_exactly, matching_presets))
        if len(matching_presets) != 1:
            raise CurryError("That doesn't look like a seed or preset. Curry.")
        matching_preset = matching_presets[0]
        _, descriptor = matching_preset
        return descriptor

    @classmethod
    def all_presets(cls):
        presets = cls._adrando_presets()
        presets.update(cls.MANUAL_PRESETS)
        return presets

    @classmethod
    def _adrando_presets(cls):
        return dict(
            (preset_name, (description, FromPresetRandomizerParams(preset_name), NoRestrictionsSeedValidator()))
            for preset_name, description
            in cls.ADRANDO_PRESETS.items())


class RandoCommandHandler:
    RANDO_LINKS = [SeedsGenerator.RANDO_BASE]

    def __init__(self, args):
        self._args = args

    def handle(self):
        if len(self._args) == 0:
            return self._current_rando_seed_links()
        preset_name = self._args[0]
        if preset_name.startswith('preset'):
            return self._available_presets()
        else:
            return self._generate_seeds(preset_name)

    def _current_rando_seed_links(self):
        return ['Current rando seed links:'] + [f"Seed {i + 1}: <{link}>" for i, link in enumerate(self.RANDO_LINKS)]

    def _available_presets(self):
        return [
            f"Preset: {preset}, Description: {description}"
            for preset, (description, _, _)
            in AdRandomizerParamsDescriptorSelector.all_presets().items()
            ]

    def _generate_seeds(self, preset_name):
        try:
            params_descriptor = AdRandomizerParamsDescriptorSelector.select(preset_name)
            description, params, validator = params_descriptor
            seeds_number = self._parse_seeds_number()
            RandoCommandHandler.RANDO_LINKS = SeedsGenerator(params, validator, seeds_number).generate()
            return [f"Generating {seeds_number} {description} seeds...", "Rando seed links updated"] + \
                self._current_rando_seed_links()
        except CurryError as exc:
            return [exc.error_message, "Rando seed links NOT updated"]

    def _parse_seeds_number(self):
        DEFAULT_SEEDS_NUMBER = 3
        MAX_SEEDS_NUMBER = 7

        if len(self._args) < 2:
            return DEFAULT_SEEDS_NUMBER
        seeds_number_string = self._args[1]
        try:
            seeds_number = int(seeds_number_string)
            if 1 <= seeds_number <= MAX_SEEDS_NUMBER:
                return seeds_number
            else:
                raise CurryError(f'Number of seeds is limited to {MAX_SEEDS_NUMBER}.')
        except ValueError:
            raise CurryError(f"I don't know how to generate {seeds_number_string} seeds. Type '!help rando' for help.")
