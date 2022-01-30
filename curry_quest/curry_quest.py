from curry_quest import discord_helpers
from curry_quest.controller import Controller, Config
from discord import Message, User
import logging
import re
import traceback
import sys

logger = logging.getLogger(__name__)


class CurryQuest:
    def __init__(self, controller: Controller, config: Config):
        self._controller = controller
        self._config = config
        self._send_admin_message = lambda s: None

    def start(self, send_message_function, send_admin_message_function):
        self._send_admin_message = send_admin_message_function
        self._controller.set_response_event_handler(send_message_function)
        self._controller.set_admin_response_event_handler(send_admin_message_function)
        self._controller.start_timers()

    def is_curry_quest_message(self, message: Message):
        message_channel_id = self._message_channel_id(message)
        return message_channel_id == self._config.channel_id or message_channel_id == self._config.admin_channel_id

    def _message_channel_id(self, message: Message):
        return message.channel.id

    def process_message(self, message: Message):
        parsed_message = self._parse_message(message)
        if parsed_message is None:
            return
        command, args, player_id = parsed_message
        try:
            if self._is_admin_message(message):
                self._process_admin_message(player_id, command, args)
            else:
                self._process_user_message(player_id, command, args)
        except:
            for line in traceback.format_exception(*sys.exc_info()):
                logger.error(line.strip())

    def _parse_message(self, message: Message):
        splitted_message = message.content.split()
        if len(splitted_message) == 0:
            return
        command = splitted_message[0]
        if not command.startswith('!'):
            return
        command = command[1:]
        args = splitted_message[1:]
        player_id = self._player_id(message.author)
        return command, args, player_id

    def _is_admin_message(self, message: Message):
        return self._message_channel_id(message) == self._config.admin_channel_id

    def _process_admin_message(self, player_id, command, args):
        if not self._is_admin(player_id):
            return
        mention_string = discord_helpers.user_mention(player_id)
        parsed_admin_args = self._parse_admin_args(args)
        if parsed_admin_args is None:
            self._send_admin_message(f"{mention_string}: Command is missing target player id.")
            return
        target_player_id, args = parsed_admin_args
        if self._controller.handle_admin_action(target_player_id, command, args):
            self._send_admin_message(f"{mention_string}: Admin command handled.")
        else:
            self._send_admin_message(
                f"{mention_string}: {discord_helpers.user_mention(target_player_id)} did not join the quest.")

    def _parse_admin_args(self, args):
        if len(args) == 0:
            return
        match = re.match(r'<@!(\d+)>', args[0])
        if not match:
            return
        return int(match.group(1)), args[1:]

    def _is_admin(self, player_id):
        return player_id in self._config.admins

    def _process_user_message(self, player_id, command, args):
        if command == 'join':
            self._controller.add_player(player_id)
        elif command == 'leave':
            self._controller.remove_player(player_id)
        else:
            self._controller.handle_user_action(player_id, command, args)

    def _player_id(self, user: User) -> int:
        return user.id
