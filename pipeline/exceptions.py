class TaskError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.message = message
        self.errors = errors


class DuplicatedTaskError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(f"There are duplicated task ids: {message}")
        self.message = message
        self.errors = errors
