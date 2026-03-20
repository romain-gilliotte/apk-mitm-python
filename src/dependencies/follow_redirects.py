import threading
import urllib.request
import urllib.error


class _Chunk:
    def __init__(self, data):
        self._data = data
        self.byteLength = len(data)


class _Response:
    def __init__(self, status_code, headers):
        self.statusCode = status_code
        self.headers = headers
        self._listeners = {}
        self._destroyed = False
        self._pipe_target = None
        self._pending_error = None

    def on(self, event, callback):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        return self

    def _emit(self, event, *args):
        for cb in self._listeners.get(event, []):
            cb(*args)

    def destroy(self, error=None):
        self._destroyed = True
        if error is not None:
            self._pending_error = error

    def pipe(self, file_stream):
        self._pipe_target = file_stream
        return file_stream


class _Request:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        return self

    def _emit(self, event, *args):
        for cb in self._listeners.get(event, []):
            cb(*args)


def _make_response(http_response):
    headers = {}
    for key, value in http_response.getheaders():
        headers[key.lower()] = value
    return _Response(http_response.status, headers), http_response


class _Https:
    def get(self, url, callback):
        request = _Request()

        def _do_request():
            try:
                req = urllib.request.Request(url, method='GET')
                try:
                    http_response = urllib.request.urlopen(req)
                except urllib.error.HTTPError as e:
                    http_response = e

                response, raw = _make_response(http_response)
                callback(response)

                try:
                    if response._pending_error is not None:
                        response._emit('error', response._pending_error)
                        return

                    if response._destroyed:
                        return

                    while True:
                        if response._destroyed:
                            return

                        chunk_data = raw.read(8192)
                        if not chunk_data:
                            break

                        chunk = _Chunk(chunk_data)
                        response._emit('data', chunk)

                        if response._pipe_target is not None:
                            response._pipe_target.write(chunk_data)

                    if response._pipe_target is not None:
                        response._pipe_target.close()
                finally:
                    raw.close()

            except Exception as e:
                request._emit('error', e)

        thread = threading.Thread(target=_do_request, daemon=True)
        thread.start()

        return request


https = _Https()
