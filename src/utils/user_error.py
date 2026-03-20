# Class for custom errors that can be shown directly to users of the CLI
# without displaying the entire stack trace.
class UserError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.name = UserError.__name__
