from curry_quest import commands
from curry_quest.state_base import StateBase
from curry_quest.unit import Unit
from curry_quest.statuses import Statuses


class StateTrapEvent(StateBase):
    def __init__(self, context, trap=None):
        super().__init__(context)
        self._trap = trap

    def on_enter(self):
        trap = self._select_trap()
        trap_handler = self.TRAPS[trap]
        command, response = trap_handler(self)
        self._context.add_response(f'You stepped on a {trap} trap! {response}')
        self._context.generate_action(command)

    def _select_trap(self):
        return self._trap or self._context.random_selection_with_weights(self.game_config.traps_weights)

    def _familiar(self) -> Unit:
        return self._context.familiar

    def _handle_poison_trap(self):
        poison_hp_fraction = 0.2
        lost_hp = int(self._familiar().hp * poison_hp_fraction)
        lost_hp = max(lost_hp, 1)
        if lost_hp >= self._familiar().hp:
            lost_hp = self._familiar(). hp - 1
        self._familiar().deal_damage(lost_hp)
        return commands.EVENT_FINISHED, f'Noxious fumes fill your lungs. You lose {lost_hp} HP.'

    def _handle_sleep_trap(self):
        self._familiar().set_status(Statuses.Sleep)
        return commands.EVENT_FINISHED, 'You feel a bit drowsy.'

    def _handle_upheaval_trap(self):
        self._familiar().set_status(Statuses.Upheavel)
        return commands.EVENT_FINISHED, 'The ground suddenly rises under your feet.'

    def _handle_crack_trap(self):
        self._familiar().set_status(Statuses.Crack)
        return commands.EVENT_FINISHED, 'The ground collapses around you, leaving you in a pit.'

    def _handle_go_up_trap(self):
        return commands.GO_UP, 'A giant spring throws you up to the next floor.'

    def _handle_paralyze_trap(self):
        self._familiar().set_status(Statuses.Paralyze)
        return commands.EVENT_FINISHED, 'Your muscles tighten up. Movement is difficult.'

    def _handle_blinder_trap(self):
        self._familiar().set_status(Statuses.Blind)
        return commands.EVENT_FINISHED, 'Your eyes get cloudy and you\'re unable to see.'

    TRAPS = {
        'Poison': _handle_poison_trap,
        'Sleep': _handle_sleep_trap,
        'Upheaval': _handle_upheaval_trap,
        'Crack': _handle_crack_trap,
        'Go up': _handle_go_up_trap,
        'Paralyze': _handle_paralyze_trap,
        'Blinder': _handle_blinder_trap
    }

    @classmethod
    def _parse_args(cls, context, args):
        if len(args) == 0:
            return ()
        trap = args[0].lower().capitalize()
        if trap not in cls.TRAPS.keys():
            raise cls.ArgsParseError('Unknown trap')
        return trap,
