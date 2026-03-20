from __future__ import annotations

import asyncio
import sys
from typing import Any, Callable, TypedDict, List


class ListrEvent(TypedDict, total=False):
    type: str
    data: Any


class _State:
    PENDING = 0
    COMPLETED = 1
    FAILED = 2
    SKIPPED = 3

    @staticmethod
    def to_string(value):
        if value == _State.PENDING:
            return "pending"
        elif value == _State.COMPLETED:
            return "completed"
        elif value == _State.FAILED:
            return "failed"
        elif value == _State.SKIPPED:
            return "skipped"
        else:
            return "unknown"


class ListrError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.name = "ListrError"
        self.errors = []
        self.context = None


class ListrTaskObject:
    def __init__(self, listr, task, options):
        self._listr = listr
        self._options = options or {}
        self._subtasks = []
        self._enabled_fn = task.get("enabled")
        self._is_enabled = True
        self._state = None
        self._subscribers = []

        self.output = None
        self.title = task["title"]
        self.skip = task.get("skip", lambda *args: False)
        self.task = task["task"]

    @property
    def subtasks(self):
        return self._subtasks

    def _set_state(self, state):
        self._state = state
        self._notify({"type": "STATE"})

    @property
    def state(self):
        return _State.to_string(self._state)

    def check(self, ctx):
        if self._state is None and self._enabled_fn:
            is_enabled = self._enabled_fn(ctx)
            if self._is_enabled != is_enabled:
                self._is_enabled = is_enabled
                self._notify({"type": "ENABLED", "data": is_enabled})

    def has_subtasks(self):
        return len(self._subtasks) > 0

    def is_pending(self):
        return self._state == _State.PENDING

    def is_skipped(self):
        return self._state == _State.SKIPPED

    def is_completed(self):
        return self._state == _State.COMPLETED

    def is_enabled(self):
        return self._is_enabled

    def has_failed(self):
        return self._state == _State.FAILED

    # Alias methods matching JS naming used in observe-listr.ts
    def isPending(self):
        return self.is_pending()

    def isSkipped(self):
        return self.is_skipped()

    def isCompleted(self):
        return self.is_completed()

    def isEnabled(self):
        return self.is_enabled()

    def hasFailed(self):
        return self.has_failed()

    def hasSubtasks(self):
        return self.has_subtasks()

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def _notify(self, event):
        for cb in self._subscribers:
            cb(event)

    def _complete(self):
        pass

    async def run(self, context, wrapper):
        try:
            self._set_state(_State.PENDING)
            skipped = self.skip(context)
            if asyncio.iscoroutine(skipped) or asyncio.isfuture(skipped):
                skipped = await skipped

            if skipped:
                if isinstance(skipped, str):
                    self.output = skipped
                self._set_state(_State.SKIPPED)
                return

            result = self.task(context, wrapper)
            await self._handle_result(result, context)

            if self.is_pending():
                self._set_state(_State.COMPLETED)
        except ListrError as error:
            self._set_state(_State.FAILED)
            wrapper.report(error)
        except Exception as error:
            self._set_state(_State.FAILED)

            if not self.has_subtasks():
                self.output = str(error)

            self._notify({"type": "DATA", "data": str(error)})
            wrapper.report(error)

            if self._listr._exit_on_error is not False:
                raise
        finally:
            self._complete()

    async def _handle_result(self, result, context):
        if asyncio.iscoroutine(result) or asyncio.isfuture(result):
            result = await result
            await self._handle_result(result, context)
            return

        if _is_listr(result):
            result._options = {**self._options, **result._options}
            result._exit_on_error = result._options.get("exitOnError")
            result.set_renderer("silent")
            self._subtasks = result.tasks
            self._notify({"type": "SUBTASKS"})
            await result.run(context)
            return

        if _is_observable(result):
            loop = asyncio.get_running_loop()
            future = loop.create_future()

            def on_next(data):
                self.output = data
                self._notify({"type": "DATA", "data": data})

            def on_error(err):
                loop.call_soon_threadsafe(lambda: future.done() or future.set_exception(err))

            def on_complete():
                loop.call_soon_threadsafe(lambda: future.done() or future.set_result(None))

            result.subscribe(
                on_next=on_next,
                on_error=on_error,
                on_complete=on_complete,
            )
            await future
            return

        return result


def _is_listr(obj):
    return (
        obj is not None
        and hasattr(obj, "set_renderer")
        and hasattr(obj, "add")
        and hasattr(obj, "run")
    )


def _is_observable(obj):
    return obj is not None and hasattr(obj, "subscribe") and not _is_listr(obj)


class ListrTaskWrapper:
    def __init__(self, task, errors):
        self._task = task
        self._errors = errors

    @property
    def title(self):
        return self._task.title

    @title.setter
    def title(self, value):
        self._task.title = value
        self._task._notify({"type": "TITLE", "data": value})

    @property
    def output(self):
        return self._task.output

    @output.setter
    def output(self, data):
        self._task.output = data
        self._task._notify({"type": "DATA", "data": data})

    def report(self, error):
        if isinstance(error, ListrError):
            for err in error.errors:
                self._errors.append(err)
        else:
            self._errors.append(error)

    def skip(self, message=None):
        if message is not None and not isinstance(message, str):
            raise TypeError(
                f"Expected `message` to be of type `string`, got `{type(message).__name__}`"
            )

        if message:
            self._task.output = message

        self._task._set_state(_State.SKIPPED)

    async def run(self, ctx=None):
        return await self._task.run(ctx, self)


class _SilentRenderer:
    nonTTY = True

    def __init__(self, tasks, options):
        pass

    def render(self):
        pass

    def end(self, error=None):
        pass


class _VerboseRenderer:
    nonTTY = True

    def __init__(self, tasks, options):
        self._tasks = tasks
        self._options = options

    def render(self):
        self._render_tasks(self._tasks)

    def _render_tasks(self, tasks):
        for task in tasks:
            def make_handler(t):
                def handler(event):
                    if event["type"] == "SUBTASKS":
                        self._render_tasks(t.subtasks)
                        return
                    if event["type"] == "STATE":
                        message = "started" if t.is_pending() else t.state
                        print(f"  {t.title} [{message}]")
                        if t.is_skipped() and t.output:
                            print(f"  -> {t.output}")
                    elif event["type"] == "DATA":
                        print(f"  -> {event.get('data', '')}")
                    elif event["type"] == "TITLE":
                        print(f"  {t.title} [title changed]")
                return handler
            task.subscribe(make_handler(task))

    def end(self, error=None):
        pass


class _DefaultRenderer:
    nonTTY = False

    def __init__(self, tasks, options):
        self._tasks = tasks
        self._options = options

    def render(self):
        self._render_tasks(self._tasks)

    def _render_tasks(self, tasks):
        for task in tasks:
            def make_handler(t):
                def handler(event):
                    if event["type"] == "SUBTASKS":
                        self._render_tasks(t.subtasks)
                        return
                    if event["type"] == "STATE":
                        if t.is_pending():
                            print(f"  [started] {t.title}")
                        elif t.is_skipped():
                            print(f"  [skipped] {t.title}")
                            if t.output:
                                print(f"    -> {t.output}")
                        elif t.is_completed():
                            print(f"  [completed] {t.title}")
                        elif t.has_failed():
                            print(f"  [failed] {t.title}")
                    elif event["type"] == "DATA":
                        data = event.get("data", "")
                        if data:
                            print(f"    -> {data}")
                return handler
            task.subscribe(make_handler(task))

    def end(self, error=None):
        pass


_renderers = {
    "silent": _SilentRenderer,
    "verbose": _VerboseRenderer,
    "default": _DefaultRenderer,
}


def _is_renderer_supported(renderer_cls):
    return (sys.stdout.isatty()) or (getattr(renderer_cls, "nonTTY", False) is True)


def _get_renderer_class(renderer):
    if isinstance(renderer, str):
        return _renderers.get(renderer, _renderers["default"])
    if isinstance(renderer, type):
        return renderer
    return _renderers["default"]


def _get_renderer(renderer, fallback_renderer=None):
    ret = _get_renderer_class(renderer)
    if not _is_renderer_supported(ret):
        ret = _get_renderer_class(fallback_renderer)
        if not ret or not _is_renderer_supported(ret):
            ret = _renderers["verbose"]
    return ret


class _ListrTaskRequired(TypedDict):
    title: str
    task: Callable

class ListrTask(_ListrTaskRequired, total=False):
    skip: Callable
    enabled: Callable


class ListrRenderer:
    def render(self):
        raise NotImplementedError

    def end(self, error=None):
        raise NotImplementedError


class Listr:
    def __init__(self, tasks=None, options=None):
        if tasks is not None and not isinstance(tasks, list) and isinstance(tasks, dict):
            if isinstance(tasks.get("title"), str) and callable(tasks.get("task")):
                raise TypeError(
                    "Expected an array of tasks or an options object, got a task object"
                )
            options = tasks
            tasks = []

        if tasks is not None and not isinstance(tasks, list):
            raise TypeError("Expected an array of tasks")

        self._options = {
            "showSubtasks": True,
            "concurrent": False,
            "renderer": "default",
            "nonTTYRenderer": "verbose",
            **(options or {}),
        }
        self._tasks: List[ListrTaskObject] = []

        self.concurrency = 1
        concurrent = self._options.get("concurrent")
        if concurrent is True:
            self.concurrency = float("inf")
        elif concurrent is not False and isinstance(concurrent, (int, float)):
            self.concurrency = concurrent

        self._renderer_class = _get_renderer(
            self._options.get("renderer"),
            self._options.get("nonTTYRenderer"),
        )

        self._exit_on_error = self._options.get("exitOnError")
        self._renderer = None

        self.add(tasks or [])

    def _check_all(self, context):
        for task in self._tasks:
            task.check(context)

    @property
    def tasks(self):
        return self._tasks

    def set_renderer(self, value):
        self._renderer_class = _get_renderer(value)

    # Alias matching JS naming used in observe-listr.ts
    def setRenderer(self, value):
        self.set_renderer(value)

    def add(self, task):
        tasks = task if isinstance(task, list) else [task]
        for t in tasks:
            self._tasks.append(ListrTaskObject(self, t, self._options))
        return self

    def render(self):
        if not self._renderer:
            self._renderer = self._renderer_class(self._tasks, self._options)
        return self._renderer.render()

    async def run(self, context=None):
        self.render()

        if context is None:
            context = {}

        errors = []

        self._check_all(context)

        try:
            if self.concurrency == 1:
                for task in self._tasks:
                    self._check_all(context)
                    if not task.is_enabled():
                        continue
                    wrapper = ListrTaskWrapper(task, errors)
                    await wrapper.run(context)
            else:
                async def run_task(task):
                    if not task.is_enabled():
                        return
                    wrapper = ListrTaskWrapper(task, errors)
                    await wrapper.run(context)

                tasks = [run_task(task) for task in self._tasks]
                await asyncio.gather(*tasks)

            if len(errors) > 0:
                err = ListrError("Something went wrong")
                err.errors = errors
                raise err

            self._renderer.end()

            return context

        except Exception as error:
            if not hasattr(error, "context"):
                error.context = context
            self._renderer.end(error)
            raise
