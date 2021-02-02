import time
import math


class CurryError(BaseException):
    def __init__(self, error_message):
        self.error_message = error_message


class SeedGenerator:
    RANDO_BASE = 'https://adrando.com/'

    def __init__(self, randomizer_params, seeds_number):
        self._randomizer_params = randomizer_params
        self._seeds_number = seeds_number

    def generate(self):
        seed_base = time.time() * 1000
        seed_floor = math.floor(seed_base)
        # Use the nanosecond portion of the time as a pseudo-random offset, plus a constant in case that happens to be 0
        offset = math.floor((seed_base - seed_floor) * 1000) + 50
        return [self._create_adrando_link(seed_floor - offset * i) for i in range(self._seeds_number)]

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


class AdRandomizerParamsDescriptorSelector:
    ADRANDO_PRESETS = {
        'secondTower': 'Only Second Tower',
        'secondTowerRun': 'Speedrun Second Tower',
        'starsTournament': 'STARS Tournament',
        'tournament': 'RM3T #2 Tournament'
    }
    MANUAL_PRESETS = {
        'randomToolkit': ('RM3T #3 Random Toolkit Tournament', ManualRandomizerParams('dE:-2,fh:1,iInS:0,txX'))
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
            (preset_name, (description, FromPresetRandomizerParams(preset_name)))
            for preset_name, description
            in cls.ADRANDO_PRESETS.items())


class RandoCommandHandler:
    RANDO_LINKS = [SeedGenerator.RANDO_BASE]

    def __init__(self, ctx, args):
        self._ctx = ctx
        self._args = args

    async def handle(self):
        if len(self._args) == 0:
            await self._print_current_rando_seed_links()
            return
        preset_name = self._args[0]
        if preset_name.startswith('preset'):
            await self._print_presets()
        else:
            await self._generate_and_print_seeds(preset_name)

    async def _print_current_rando_seed_links(self):
        await self._ctx.send(curry_message("Current rando seed links:"))
        await self._ctx.send(
            '\n'.join(
                curry_message(f"Seed {i + 1}: <{link}>")
                for i, link
                in enumerate(self.RANDO_LINKS)))

    async def _print_presets(self):
        await self._ctx.send(
            '\n'.join(
                curry_message(f"Preset: {preset}, Description: {description}")
                for preset, (description, _)
                in AdRandomizerParamsDescriptorSelector.all_presets().items()))

    async def _generate_and_print_seeds(self, preset_name):
        try:
            params_descriptor = AdRandomizerParamsDescriptorSelector.select(preset_name)
            description, params = params_descriptor
            seeds_number = self._parse_seeds_number()
            await ctx.send(curry_message(f"Generating {seeds_number} {description} seeds..."))
            RandoCommandHandler.RANDO_LINKS = SeedGenerator(params, seeds_number).generate()
            await ctx.send(curry_message("Rando seed links updated"))
            await ctx.send(curry_message("Current rando seed links:"))
            await ctx.send(
                '\n'.join(
                    curry_message(f"Seed {i + 1}: <{link}>")
                    for i, link
                    in enumerate(self.RANDO_LINKS)))
        except CurryError as exc:
            await self._ctx.send(curry_message(exc.error_message))
            await ctx.send(curry_message("Rando seed links NOT updated"))

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
