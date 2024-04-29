class SuitHook:
    def __init__(self, call_fn):
        self.call = call_fn
        self.name = call_fn.__name__

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


def hook(*args, **kwargs):
    def decorator(fn):
        return SuitHook(fn)

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        # called as @hook
        return SuitHook(args[0])
    else:
        # called as @hook(*args, **kwargs)
        return decorator
