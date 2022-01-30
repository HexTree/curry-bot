from curry_quest import commands
from curry_quest.items import normalize_item_name, all_items
from curry_quest.state_base import StateBase
from curry_quest.state_with_inventory_item import StateWithInventoryItem


class StateItemEvent(StateBase):
    def __init__(self, context, item=None):
        super().__init__(context)
        self._item = item

    def on_enter(self):
        item = self._select_item()
        self._context.buffer_item(item)
        self._context.add_response(f"You come across a {item.name}. Do you want to pick it up?")

    def _select_item(self):
        return self._item or self._context.random_selection_with_weights(self._found_items_weights())

    def _found_items_weights(self):
        return dict((item, self.game_config.found_items_weights[item.name]) for item in all_items())

    def is_waiting_for_user_action(self) -> bool:
        return True

    @classmethod
    def _parse_args(cls, context, args):
        if len(args) == 0:
            return ()
        item_name = normalize_item_name(*args)
        for item in all_items():
            if normalize_item_name(item.name).startswith(item_name):
                return item,
        raise cls.ArgsParseError('Unknown item')


class StateItemPickUp(StateBase):
    def on_enter(self):
        if not self.inventory.is_full():
            item = self._context.take_buffered_item()
            self.inventory.add_item(item)
            self._context.add_response(f"You take the {item.name} with you.")
            self._context.generate_action(commands.ITEM_PICKED_UP)
        else:
            items = ', '.join(self.inventory.items)
            self._context.add_response(
                f"Your inventory is full. You need to drop one of your current items first. You have: {items}.")


class StateItemPickUpFullInventory(StateWithInventoryItem):
    def on_enter(self):
        dropped_item = self.inventory.take_item(self._item_index)
        picked_up_item = self._context.take_buffered_item()
        self.inventory.add_item(picked_up_item)
        self._context.add_response(f"You drop a {dropped_item.name} and take a {picked_up_item.name} instead.")
        self._context.generate_action(commands.ITEM_PICKED_UP)


class StateItemPickUpIgnored(StateBase):
    def on_enter(self):
        item = self._context.take_buffered_item()
        self._context.add_response(f"You leave the {item.name} on the ground and leave.")
        self._context.generate_action(commands.EVENT_FINISHED)


class StateItemEventFinished(StateBase):
    def on_enter(self):
        self._context.clear_item_buffer()
        self._context.generate_action(commands.EVENT_FINISHED)
