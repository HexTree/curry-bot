from curry_quest.state_base import StateBase


class StateWithMonster(StateBase):
    def __init__(self, context, monster_name: str=None):
        super().__init__(context)
        self._monster_name = monster_name

    @classmethod
    def _parse_args(cls, context, args):
        if len(args) == 0:
            return ()
        monster_name = args[0]
        if monster_name not in context.game_config.monsters_traits.keys():
            raise cls.ArgsParseError('Unknown monster')
        return monster_name,
