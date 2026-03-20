import tempfile
import uuid
import os


class _Tempy:
    def directory(self, options=None):
        prefix = options.get('prefix', '') if options else ''
        directory = os.path.join(tempfile.gettempdir(), prefix + uuid.uuid4().hex)
        os.makedirs(directory)
        return directory


tempy = _Tempy()
