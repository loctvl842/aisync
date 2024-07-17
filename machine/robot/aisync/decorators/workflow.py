class SuitWorkflow:
    def __init__(self, call_fn):
        self.call = call_fn
        self.name = call_fn.__name__

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.name}>"


def workflow(*args, **kwargs):
    def decorator(fn):
        return SuitWorkflow(fn)

    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        # called as @workflow
        return SuitWorkflow(args[0])
    else:
        # called as @workflow(*args, **kwargs)
        return decorator
