import asyncio
from functools import wraps


def no_op_decorator(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        return await fn(*args, **kwargs)

    return wrapper


async def parallel_do(
    arr: list[any],
    callback: callable,
    limit: int = 100,
    decorator=no_op_decorator,
    lock: asyncio.Lock | None = None,
    **kwargs
):
    """ """
    if lock is None:
        lock = asyncio.Lock()

    @decorator
    async def do_batch(batch, **dkwargs):
        tasks = [asyncio.create_task(callback(item, lock=lock, **dkwargs, **kwargs)) for item in batch]
        return await asyncio.gather(*tasks)

    batches = [arr[i : i + limit] for i in range(0, len(arr), limit)]
    results = []
    for batch in batches:
        batch_results = await do_batch(batch)
        results.extend(batch_results)
    return results
