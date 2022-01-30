import enum


class Genus(enum.Enum):
    Empty = 0
    Fire = 1
    Water = 2
    Wind = 3

    def is_strong_against(self, other) -> bool:
        if self is Genus.Fire:
            return other is Genus.Wind
        elif self is Genus.Water:
            return other is Genus.Fire
        elif self is Genus.Wind:
            return other is Genus.Water
        elif self is Genus.Empty:
            return False
        else:
            raise ValueError(f'Unknown Genus type "{self}"')

    def is_weak_against(self, other) -> bool:
        if self is Genus.Fire:
            return other is Genus.Water
        elif self is Genus.Water:
            return other is Genus.Wind
        elif self is Genus.Wind:
            return other is Genus.Fire
        elif self is Genus.Empty:
            return False
        else:
            raise ValueError(f'Unknown Genus type "{self}"')
