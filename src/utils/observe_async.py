import asyncio

from src.dependencies.rxjs import Observable

# Wraps an async function and produces an `Observable` that reacts to the
# function resolving (`complete` notification), rejecting (`error`
# notification), and calling the `next` callback (`next` notification), making
# it easier to write `async`/`await`-based code that reports its progress
# through an `Observable` *without* forgetting to handle errors.
def observe_async(fn):
    def subscribe_fn(subscriber):
        async def run():
            try:
                await fn(lambda value: subscriber.next(value))
                subscriber.complete()
            except Exception as error:
                subscriber.error(error)
        asyncio.ensure_future(run())
    return Observable(subscribe_fn)
