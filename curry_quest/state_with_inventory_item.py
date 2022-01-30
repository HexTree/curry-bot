from curry_quest.items import normalize_item_name
from curry_quest.state_base import StateBase


class StateWithInventoryItem(StateBase):
    def __init__(self, context, item_index: int):
        super().__init__(context)
        self._item_index = item_index

    @classmethod
    def _parse_args(cls, context, args):
        if len(args) < 1:
            raise cls.ArgsParseError('You need to specify item.')
        item_name = normalize_item_name(*args)
        try:
            index, _ = context.inventory.find_item(item_name)
        except ValueError:
            raise cls.ArgsParseError(f'You do not have "{item_name}" in your inventory.')
        return (index,)
