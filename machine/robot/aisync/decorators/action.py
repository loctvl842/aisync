class SuitAction:
    def __init__(self, call_fn):
        self.call = call_fn
        self.name = call_fn.__name__

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


def action(*args, **kwargs):
    def decorator(call_fn):
        return SuitAction(call_fn)

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        # called as @plugin
        return SuitAction(args[0])
    else:
        # called as @plugin(*args, **kwargs)
        return decorator
