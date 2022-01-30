import datetime
import json
from curry_quest import commands
from curry_quest.errors import InvalidOperation
from curry_quest.items import normalize_item_name, all_items
from curry_quest.state_base import StateBase
from curry_quest.state_battle import StateBattleEvent, StateStartBattle, StateBattlePreparePhase, StateBattleApproach, \
    StateBattlePhase, StateBattlePlayerTurn, StateEnemyStats, StateBattleAttack, StateBattleUseSpell, \
    StateBattleUseItem, StateBattleTryToFlee, StateBattleEnemyTurn
from curry_quest.state_character import StateCharacterEvent, StateItemTrade, StateItemTradeAccepted, \
    StateItemTradeRejected, StateFamiliarTrade, StateFamiliarTradeAccepted, StateFamiliarTradeRejected, \
    StateEvolveFamiliar
from curry_quest.state_elevator import StateElevatorEvent, StateGoUp, StateElevatorOmitted, StateNextFloor
from curry_quest.state_event import StateWaitForEvent, StateGenerateEvent
from curry_quest.state_familiar import StateFamiliarEvent, StateMetFamiliarIgnore, StateFamiliarFusion, \
    StateFamiliarReplacement
from curry_quest.state_initialize import StateInitialize, StateEnterTower
from curry_quest.state_item import StateItemEvent, StateItemPickUp, StateItemPickUpFullInventory, StateItemPickUpIgnored, \
    StateItemEventFinished
from curry_quest.state_machine_action import StateMachineAction
from curry_quest.state_machine_context import StateMachineContext
from curry_quest.state_trap import StateTrapEvent
import logging

logger = logging.getLogger(__name__)


class Transition:
    def __init__(self, nextState: StateBase, guard):
        self.nextState = nextState
        self.guard = guard

    @classmethod
    def _action_by_admin_guard(cls, action):
        return action.is_given_by_admin

    @classmethod
    def _no_guard(cls, action):
        return True

    @classmethod
    def by_admin(cls, nextState: StateBase):
        return Transition(nextState, guard=cls._action_by_admin_guard)

    @classmethod
    def by_user(cls, nextState):
        return Transition(nextState, guard=cls._no_guard)


class StateStart(StateBase):
    pass


class StateGameOver(StateBase):
    pass


class StateMachine:
    VERSION = 2
    TRANSITIONS = {
        StateStart: {commands.STARTED: Transition.by_admin(StateInitialize)},
        StateInitialize: {commands.ENTER_TOWER: Transition.by_user(StateEnterTower)},
        StateEnterTower: {commands.ENTERED_TOWER: Transition.by_admin(StateGenerateEvent)},
        StateWaitForEvent: {
            commands.GENERATE_EVENT: Transition.by_admin(StateGenerateEvent),
            commands.BATTLE_EVENT: Transition.by_admin(StateBattleEvent),
            commands.ITEM_EVENT: Transition.by_admin(StateItemEvent),
            commands.TRAP_EVENT: Transition.by_admin(StateTrapEvent),
            commands.CHARACTER_EVENT: Transition.by_admin(StateCharacterEvent),
            commands.ELEVATOR_EVENT: Transition.by_admin(StateElevatorEvent),
            commands.FAMILIAR_EVENT: Transition.by_admin(StateFamiliarEvent)
        },
        StateGenerateEvent: {commands.EVENT_GENERATED: Transition.by_admin(StateWaitForEvent)},
        StateBattleEvent: {commands.START_BATTLE: Transition.by_admin(StateStartBattle)},
        StateStartBattle: {commands.BATTLE_PREPARE_PHASE: Transition.by_admin(StateBattlePreparePhase)},
        StateBattlePreparePhase: {
            commands.USE_ITEM: Transition.by_user(StateBattleUseItem),
            commands.APPROACH: Transition.by_user(StateBattleApproach),
            commands.BATTLE_PREPARE_PHASE_FINISHED: Transition.by_admin(StateBattlePhase)
        },
        StateBattleApproach: {commands.BATTLE_PREPARE_PHASE_FINISHED: Transition.by_admin(StateBattlePhase)},
        StateBattlePhase: {
            commands.PLAYER_TURN: Transition.by_admin(StateBattlePlayerTurn),
            commands.ENEMY_TURN: Transition.by_admin(StateBattleEnemyTurn),
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent),
            commands.YOU_DIED: Transition.by_admin(StateGameOver)
        },
        StateBattlePlayerTurn: {
            commands.ENEMY_STATS: Transition.by_user(StateEnemyStats),
            commands.ATTACK: Transition.by_user(StateBattleAttack),
            commands.USE_SPELL: Transition.by_user(StateBattleUseSpell),
            commands.USE_ITEM: Transition.by_user(StateBattleUseItem),
            commands.FLEE: Transition.by_user(StateBattleTryToFlee)
        },
        StateEnemyStats: {commands.PLAYER_TURN: Transition.by_admin(StateBattlePlayerTurn)},
        StateBattleAttack: {commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattlePhase)},
        StateBattleUseSpell: {
            commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattlePhase),
            commands.CANNOT_USE_SPELL: Transition.by_admin(StateBattlePlayerTurn)
        },
        StateBattleUseItem: {
            commands.BATTLE_PREPARE_PHASE_ACTION_PERFORMED: Transition.by_admin(StateBattlePreparePhase),
            commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattlePhase),
            commands.CANNOT_USE_ITEM_PREPARE_PHASE: Transition.by_admin(StateBattlePreparePhase),
            commands.CANNOT_USE_ITEM_BATTLE_PHASE: Transition.by_admin(StateBattlePlayerTurn)
        },
        StateBattleTryToFlee: {
            commands.CANNOT_FLEE: Transition.by_admin(StateBattlePlayerTurn),
            commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattlePhase),
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)
        },
        StateBattleEnemyTurn: {commands.BATTLE_ACTION_PERFORMED: Transition.by_admin(StateBattlePhase)},
        StateItemEvent: {
            commands.ACCEPTED: Transition.by_user(StateItemPickUp),
            commands.REJECTED: Transition.by_user(StateItemEventFinished)
        },
        StateItemPickUp: {
            commands.ITEM_PICKED_UP: Transition.by_admin(StateItemEventFinished),
            commands.DROP_ITEM: Transition.by_user(StateItemPickUpFullInventory),
            commands.IGNORE: Transition.by_user(StateItemPickUpIgnored)
        },
        StateItemPickUpFullInventory: {commands.ITEM_PICKED_UP: Transition.by_admin(StateItemEventFinished)},
        StateItemPickUpIgnored: {commands.EVENT_FINISHED: Transition.by_admin(StateItemEventFinished)},
        StateItemEventFinished: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateTrapEvent: {
            commands.GO_UP: Transition.by_admin(StateGoUp),
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)
        },
        StateElevatorEvent: {
            commands.ACCEPTED: Transition.by_user(StateGoUp),
            commands.REJECTED: Transition.by_user(StateElevatorOmitted)
        },
        StateGoUp: {commands.ENTERED_NEXT_FLOOR: Transition.by_admin(StateNextFloor)},
        StateElevatorOmitted: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateNextFloor: {
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent),
            commands.FINISH_GAME: Transition.by_admin(StateGameOver)
        },
        StateCharacterEvent: {
            commands.START_ITEM_TRADE: Transition.by_admin(StateItemTrade),
            commands.START_FAMILIAR_TRADE: Transition.by_admin(StateFamiliarTrade),
            commands.EVOLVE_FAMILIAR: Transition.by_admin(StateEvolveFamiliar),
            commands.START_BATTLE: Transition.by_admin(StateStartBattle),
            commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)
        },
        StateItemTrade: {
            commands.TRADE_ITEM: Transition.by_user(StateItemTradeAccepted),
            commands.REJECTED: Transition.by_user(StateItemTradeRejected)
        },
        StateItemTradeAccepted: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateItemTradeRejected: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateFamiliarTrade: {
            commands.ACCEPTED: Transition.by_user(StateFamiliarTradeAccepted),
            commands.REJECTED: Transition.by_user(StateFamiliarTradeRejected)
        },
        StateFamiliarTradeAccepted: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateFamiliarTradeRejected: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateEvolveFamiliar: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateFamiliarEvent: {
            commands.IGNORE: Transition.by_user(StateMetFamiliarIgnore),
            commands.FUSE: Transition.by_user(StateFamiliarFusion),
            commands.REPLACE: Transition.by_user(StateFamiliarReplacement)
        },
        StateMetFamiliarIgnore: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateFamiliarFusion: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateFamiliarReplacement: {commands.EVENT_FINISHED: Transition.by_admin(StateWaitForEvent)},
        StateGameOver: {commands.RESTART: Transition.by_admin(StateStart)}
    }

    def __init__(self, game_config: dict, player_id: int):
        self._context = StateMachineContext(game_config)
        self._player_id = player_id
        self._last_responses = []
        self._state = StateStart(self._context)
        self._event_selection_penalty_end_dt = None
        self._generic_actions_handlers = {
            commands.HELP: (False, self._show_available_commands),
            commands.RESTART: (True, self._restart_state_machine),
            commands.SHOW_FAMILIAR_STATS: (False, self._handle_familiar_stats_query),
            commands.SHOW_INVENTORY: (False, self._handle_inventory_query),
            commands.SHOW_FLOOR: (False, self._handle_floor_query),
            commands.SHOW_STATE: (False, self._handle_state_query),
            commands.GIVE_ITEM: (True, self._give_item),
            commands.RESTORE_HP: (True, self._restore_hp),
            commands.RESTORE_MP: (True, self._restore_mp)
        }

    @property
    def player_id(self) -> int:
        return self._player_id

    def has_event_selection_penalty(self) -> bool:
        return self._event_selection_penalty_end_dt is not None

    def clear_event_selection_penalty(self):
        self._event_selection_penalty_end_dt = None

    def set_event_selection_penalty(self, duration_in_seconds):
        self._event_selection_penalty_end_dt = datetime.datetime.now() + datetime.timedelta(seconds=duration_in_seconds)

    @property
    def event_selection_penalty_end_dt(self) -> datetime.datetime:
        return self._event_selection_penalty_end_dt

    def save(self, f):
        state_machine_json = {
            'version': self.VERSION,
            'player': self.player_id,
            'responses': self._last_responses,
            'context': self._context.to_json(),
            'state': self._state.to_json()
        }
        json.dump(state_machine_json, f)

    @classmethod
    def load(cls, f, game_config) -> '__class__':
        state_machine_json = json.load(f)
        state_machine = cls(game_config, state_machine_json['player'])
        state_machine._last_responses = state_machine_json.get('responses', [])
        state_machine._context = StateMachineContext.from_json(state_machine_json['context'], game_config)
        state_machine._state = StateBase.from_json(state_machine_json['state'], state_machine._context)
        return state_machine

    def is_started(self) -> bool:
        return type(self._state) is not StateStart

    def is_finished(self) -> bool:
        return type(self._state) is StateGameOver

    def is_waiting_for_user_action(self) -> bool:
        return self._state.is_waiting_for_user_action()

    def is_waiting_for_event(self) -> bool:
        return self._state.is_waiting_for_event()

    def on_action(self, action):
        try:
            if not self._handle_generic_action(action):
                self._handle_non_generic_action(action)
                self._last_responses = self._context.peek_responses()
        except InvalidOperation as exc:
            self._context.add_response(str(exc))
        return self._context.take_responses()

    def _handle_generic_action(self, action: StateMachineAction) -> bool:
        for command, (is_admin_command, handler) in self._generic_actions_handlers.items():
            if command == action.command:
                if not is_admin_command or action.is_given_by_admin:
                    handler(action)
                return True
        else:
            return False

    def _show_available_commands(self, action: StateMachineAction):
        available_specific_commands = self._available_specific_commands(action.is_given_by_admin)
        if len(available_specific_commands) > 0:
            self._context.add_response(f"Specific commands: {', '.join(available_specific_commands)}.")
        available_generic_commands = self._available_generic_commands(action.is_given_by_admin)
        if len(available_generic_commands) > 0:
            self._context.add_response(f"Generic commands: {', '.join(available_generic_commands)}.")

    def _restart_state_machine(self, action):
        if action.is_given_by_admin:
            self._state = StateStart(self._context)
            logger.info(f"Restarted game for {self.player_id}.")

    def _available_specific_commands(self, is_admin: bool):
        available_specific_commands = []
        for command, transition in self._current_state_transition_table().items():
            if transition.guard(StateMachineAction(command, is_given_by_admin=is_admin)):
                available_specific_commands.append(command)
        return available_specific_commands

    def _available_generic_commands(self, is_admin: bool):
        available_generic_commands = []
        for command, (is_admin_command, _) in self._generic_actions_handlers.items():
            if not is_admin_command or is_admin:
                available_generic_commands.append(command)
        return available_generic_commands

    def _handle_familiar_stats_query(self, action):
        if self._has_entered_tower():
            familiar = self._context.familiar
            self._context.add_response(f"{familiar.to_string()}.")
        else:
            self._handle_generic_action_before_entering_tower()

    def _handle_inventory_query(self, action):
        if self._has_entered_tower():
            inventory_string = ', '.join(self._context.inventory.items)
            self._context.add_response(f"You have: {inventory_string}.")
        else:
            self._handle_generic_action_before_entering_tower()

    def _handle_floor_query(self, action):
        if self._has_entered_tower():
            self._context.add_response(f"You are on {self._context.floor + 1}F.")
        else:
            self._handle_generic_action_before_entering_tower()

    def _handle_state_query(self, action):
        if not self.is_started():
            self._handle_generic_action_before_entering_tower()
        elif self.is_waiting_for_event():
            self._context.add_response(f"You are not in an event.")
        elif len(self._last_responses) == 0:
            self._context.add_response(f"There is no information about previous state.")
        else:
            for response in self._last_responses:
                self._context.add_response(response)

    def _give_item(self, action):
        if not self._has_entered_tower():
            logger.warning(f"{self.player_id} has not entered the tower yet.")
            return
        item = self._find_item(*action.args)
        if item is None:
            logger.warning(f"Item by name '{' '.join(action.args)}' does not exist.")
            return
        self._context.inventory.add_item(item)
        self._context.add_response(f"You were given {item.name} by an unknown power.")

    def _find_item(self, *item_name_parts):
        if len(item_name_parts) < 1:
            return None
        searched_item_name = normalize_item_name(*item_name_parts)
        for item in all_items():
            if normalize_item_name(item.name).startswith(searched_item_name):
                return item
        return None

    def _restore_hp(self, action):
        if not self._has_entered_tower():
            logger.warning(f"{self.player_id} has not entered the tower yet.")
            return
        self._context.familiar.restore_hp()
        self._context.add_response(f"Your HP was restored by an unknown power.")

    def _restore_mp(self, action):
        if not self._has_entered_tower():
            logger.warning(f"{self.player_id} has not entered the tower yet.")
            return
        self._context.familiar.restore_mp()
        self._context.add_response(f"Your MP was restored by an unknown power.")

    def _handle_generic_action_before_entering_tower(self):
        self._context.add_response(f"You did not enter the tower yet.")

    def _has_entered_tower(self) -> bool:
        return self.is_started() and type(self._state) is not StateInitialize

    def _handle_non_generic_action(self, action):
        state_transition_table = self._current_state_transition_table()
        if state_transition_table is None:
            self._on_unknown_state()
            return
        transition = state_transition_table.get(action.command)
        if transition is None:
            self._on_unexpected_action(action)
        else:
            self._change_state(transition, action)
            if self._context.has_action():
                self._handle_non_generic_action(self._context.take_action())

    def _current_state_transition_table(self) -> dict:
        return self.TRANSITIONS.get(type(self._state))

    def _on_unknown_state(self):
        logger.error(f"{self} is in state {self._state} for which there is no transition.")

    def _on_unexpected_action(self, action):
        logger.warning(f"{self} in state {self._state} does not have transition for '{action.command}'")

    def _change_state(self, transition, action):
        if transition.guard(action):
            self._state = transition.nextState.create(self._context, action.args)
            logger.debug(f"{self} changed state to {self._state}.")
            self._state.on_enter()

    def __str__(self):
        return f'SM for "{self.player_id}"'
