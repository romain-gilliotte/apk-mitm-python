from typing import TypeVar, Generic, Callable, Optional, Any

T = TypeVar('T')


class Subscriber(Generic[T]):
    def __init__(self):
        self._next_fn: Optional[Callable[[T], None]] = None
        self._error_fn: Optional[Callable[[Any], None]] = None
        self._complete_fn: Optional[Callable[[], None]] = None
        self._closed = False

    def next(self, value: T) -> None:
        if self._closed:
            return
        if self._next_fn is not None:
            self._next_fn(value)

    def error(self, err: Any) -> None:
        if self._closed:
            return
        self._closed = True
        if self._error_fn is not None:
            self._error_fn(err)

    def complete(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._complete_fn is not None:
            self._complete_fn()


class Observable(Generic[T]):
    def __init__(self, subscribe_fn: Optional[Callable[[Subscriber[T]], None]] = None):
        self._subscribe_fn = subscribe_fn

    def subscribe(self, observer_or_next=None, error=None, complete=None, on_next=None, on_error=None, on_complete=None):
        subscriber = Subscriber()

        if callable(observer_or_next):
            subscriber._next_fn = observer_or_next
            subscriber._error_fn = error
            subscriber._complete_fn = complete
        elif observer_or_next is not None:
            subscriber._next_fn = observer_or_next.get('next')
            subscriber._error_fn = observer_or_next.get('error')
            subscriber._complete_fn = observer_or_next.get('complete')
        elif on_next is not None or on_error is not None or on_complete is not None:
            subscriber._next_fn = on_next
            subscriber._error_fn = on_error
            subscriber._complete_fn = on_complete

        if self._subscribe_fn is not None:
            self._subscribe_fn(subscriber)

        return subscriber

    async def for_each(self, callback: Callable[[T], None]) -> None:
        import asyncio
        loop = asyncio.get_running_loop()
        future = loop.create_future()

        def on_error(err):
            loop.call_soon_threadsafe(lambda: future.done() or future.set_exception(err if isinstance(err, Exception) else Exception(str(err))))

        def on_complete():
            loop.call_soon_threadsafe(lambda: future.done() or future.set_result(None))

        self.subscribe(lambda value: callback(value), on_error, on_complete)
        await future

    def pipe(self, *operators):
        result = self
        for op in operators:
            result = op(result)
        return result


class Subject(Observable[T], Generic[T]):
    def __init__(self):
        super().__init__()
        self._subscribers: list[Subscriber[T]] = []
        self._closed = False

    def subscribe(self, observer_or_next=None, error=None, complete=None, on_next=None, on_error=None, on_complete=None):
        subscriber = Subscriber()

        if callable(observer_or_next):
            subscriber._next_fn = observer_or_next
            subscriber._error_fn = error
            subscriber._complete_fn = complete
        elif observer_or_next is not None:
            subscriber._next_fn = observer_or_next.get('next')
            subscriber._error_fn = observer_or_next.get('error')
            subscriber._complete_fn = observer_or_next.get('complete')
        elif on_next is not None or on_error is not None or on_complete is not None:
            subscriber._next_fn = on_next
            subscriber._error_fn = on_error
            subscriber._complete_fn = on_complete

        if not self._closed:
            self._subscribers.append(subscriber)

        return subscriber

    def next(self, value: T) -> None:
        if self._closed:
            return
        for sub in self._subscribers:
            sub.next(value)

    def error(self, err: Any) -> None:
        if self._closed:
            return
        self._closed = True
        for sub in self._subscribers:
            sub.error(err)

    def complete(self) -> None:
        if self._closed:
            return
        self._closed = True
        for sub in self._subscribers:
            sub.complete()


def map(project: Callable) -> Callable[[Observable], Observable]:
    def operator(source: Observable) -> Observable:
        def subscribe_fn(subscriber: Subscriber):
            source.subscribe(
                {
                    'next': lambda value: subscriber.next(project(value)),
                    'error': lambda err: subscriber.error(err),
                    'complete': lambda: subscriber.complete(),
                }
            )
        return Observable(subscribe_fn)
    return operator
