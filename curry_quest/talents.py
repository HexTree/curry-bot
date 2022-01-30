import enum


class Talents(enum.Flag):
    Empty = 0x0
    Quick = 0x1
    HpIncreased = 0x2
    MpIncreased = 0x4
    StrengthIncreased = 0x8
    Hard = 0x10
    GrowthPromoted = 0x20
    MagicAttackIncreased = 0x80
    MpConsumptionDecreased = 0x100
    ElectricShock = 0x8000
    Atrocious = 0x200000

    def has(self, talents: '__class__') -> bool:
        return (self & talents) == talents

    def clear(self, talents: '__class__'):
        self = self & (~talents)

    @classmethod
    def all(cls) -> list['__class__']:
        return [talent for talent in Talents if talent is not Talents.Empty]
