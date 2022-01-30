class StateMachineAction:
    def __init__(self, command: str, args: tuple=(), is_given_by_admin: bool=False):
        self.command = command.lower()
        self.args = args
        self.is_given_by_admin = is_given_by_admin

    def __str__(self):
        return f"{self.command}{self.args} [ADMIN: {self.is_given_by_admin}]"
