# Dependency issues for `src/utils/download_tool.py`

## `src/dependencies/rxjs.py` — Missing `for_each` method on `Observable`

The TypeScript code in `download-tool.ts` uses:

```typescript
await downloadFile(url, downloadFilePath).forEach(line => { ... })
```

RxJS `Observable.forEach()` subscribes to the observable, calls the callback for each emitted value, and returns a `Promise` that resolves when the observable completes (or rejects on error).

The Python `Observable` class in `src/dependencies/rxjs.py` does not have a `for_each` method.

### Required implementation

Add an async `for_each` method to `Observable` in `src/dependencies/rxjs.py`:

```python
async def for_each(self, callback: Callable[[T], None]) -> None:
    """Subscribe and call callback for each value. Returns awaitable that resolves on complete."""
    import asyncio
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def on_next(value):
        callback(value)

    def on_error(err):
        loop.call_soon_threadsafe(lambda: future.done() or future.set_exception(err if isinstance(err, Exception) else Exception(str(err))))

    def on_complete():
        loop.call_soon_threadsafe(lambda: future.done() or future.set_result(None))

    self.subscribe(on_next, on_error, on_complete)
    await future
```
