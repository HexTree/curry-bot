from curry_quest import commands
from curry_quest.state_base import StateBase


class StateWaitForEvent(StateBase):
    def __init__(self, context, event_command=None):
        super().__init__(context)
        self._event_command = event_command

    def on_enter(self):
        if self._event_command is not None:
            self._context.generate_action(self._event_command)

    def is_waiting_for_event(self) -> bool:
        return True

    @classmethod
    def _parse_args(cls, context, args):
        if len(args) == 0:
            return ()
        return args[0],


class StateGenerateEvent(StateBase):
    def on_enter(self):
        self._context.generate_action(commands.EVENT_GENERATED, self._select_event())

    def _select_event(self):
        return self._context.random_selection_with_weights(self.game_config.events_weights) + '_event'
