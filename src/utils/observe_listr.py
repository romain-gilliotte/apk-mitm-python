import asyncio

from src.dependencies.chalk import chalk
from src.dependencies.listr import Listr, ListrRenderer
from src.dependencies.rxjs import Observable, Subscriber

latest_subscriber: Subscriber[str] = None

def observe_listr(listr: Listr) -> Observable[str]:
    def subscribe_fn(subscriber):
        global latest_subscriber
        latest_subscriber = subscriber
        listr.setRenderer(ObservableRenderer)

        async def run_and_catch():
            try:
                await listr.run()
            except Exception:
                pass

        asyncio.ensure_future(run_and_catch())
    return Observable(subscribe_fn)

class ObservableRenderer(ListrRenderer):
    nonTTY = True

    def __init__(self, tasks, options=None):
        self._subscriber = latest_subscriber
        self._tasks = tasks

    def render(self):
        for index, task in enumerate(self._tasks):
            def make_handler(idx, t):
                def handler(event):
                    if event['type'] == 'STATE':
                        if t.isPending():
                            progress = f'{idx + 1}/{len(self._tasks)}'
                            message = chalk(f'{{dim [{progress}]}} {t.title}')
                            return self._subscriber.next(message)
                        elif t.isSkipped():
                            return self._subscriber.next(t.output or '')
                    elif event['type'] == 'DATA' and not t.hasFailed():
                        self._subscriber.next(f'{event["data"]}')
                return handler
            task.subscribe(make_handler(index, task))

    def end(self, error=None):
        if error:
            return self._subscriber.error(error)
        self._subscriber.complete()
