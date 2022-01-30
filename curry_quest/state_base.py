import copy
import jsonpickle
import logging
from curry_quest.errors import InvalidOperation
from curry_quest.state_machine_context import StateMachineContext

logger = logging.getLogger(__name__)


class StateBase:
    class ArgsParseError(Exception):
        pass

    class PreConditionsNotMet(Exception):
        pass

    def __init__(self, context: StateMachineContext):
        self._context = context

    def to_json(self):
        state_copy = copy.deepcopy(self)
        del state_copy._context
        return jsonpickle.encode(state_copy)

    @classmethod
    def from_json(cls, state_json, context: StateMachineContext):
        state = jsonpickle.decode(state_json)
        state._context = context
        return state

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def game_config(self):
        return self._context.game_config

    @property
    def inventory(self):
        return self._context.inventory

    def on_enter(self):
        logger.debug(f"{self}.on_enter()")

    def is_waiting_for_user_action(self) -> bool:
        return False

    def is_waiting_for_event(self) -> bool:
        return False

    @classmethod
    def create(cls, context, args):
        try:
            parsed_args = cls._parse_args(context, args)
            cls._verify_preconditions(context, parsed_args)
        except cls.ArgsParseError as exc:
            raise InvalidOperation(str(exc))
        except cls.PreConditionsNotMet as exc:
            raise InvalidOperation(str(exc))
        return cls(context, *parsed_args)

    @classmethod
    def _parse_args(cls, context, args):
        return ()

    @classmethod
    def _verify_preconditions(cls, context, parsed_args):
        pass

    def __str__(self):
        return self.name
