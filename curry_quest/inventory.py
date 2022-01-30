from curry_quest.errors import InvalidOperation
from curry_quest.items import normalize_item_name, Item


class Inventory:
    def __init__(self, capacity=5):
        self._capacity = capacity
        self._items: list[Item] = []

    @property
    def size(self) -> int:
        return len(self._items)

    @property
    def items(self) -> list[str]:
        return [item.name for item in self._items]

    def is_empty(self) -> bool:
        return self.size == 0

    def is_full(self) -> bool:
        return self.size >= self._capacity

    def clear(self):
        self._items.clear()

    def add_item(self, item: Item):
        if self.is_full():
            raise InvalidOperation(f"Inventory is full. Cannot add {item.name}.")
        self._items.append(item)

    def find_item(self, name) -> (int, Item):
        searched_item_name = normalize_item_name(name)
        if len(searched_item_name) == 0:
            raise ValueError()
        for index, item in enumerate(self._items):
            if normalize_item_name(item.name).startswith(searched_item_name):
                return index, item
        raise ValueError()

    def peek_item(self, index) -> Item:
        if index >= self.size:
            raise InvalidOperation(
                f"No item at index {index}. Inventory size: {self.size}.")
        return self._items[index]

    def take_item(self, index) -> Item:
        item = self.peek_item(index)
        self._items.pop(index)
        return item
