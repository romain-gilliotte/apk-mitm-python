import os
import shutil
import asyncio
from typing import Optional, Union


async def read_file(path: str, encoding: Optional[str] = None) -> Union[str, bytes]:
    loop = asyncio.get_running_loop()
    if encoding:
        def _read():
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
    else:
        def _read():
            with open(path, 'rb') as f:
                return f.read()
    return await loop.run_in_executor(None, _read)


async def write_file(path: str, data: Union[str, bytes], encoding: Optional[str] = None) -> None:
    loop = asyncio.get_running_loop()
    if isinstance(data, str):
        def _write():
            enc = encoding or 'utf-8'
            with open(path, 'w', encoding=enc) as f:
                f.write(data)
    else:
        def _write():
            with open(path, 'wb') as f:
                f.write(data)
    await loop.run_in_executor(None, _write)


async def copy_file(src: str, dest: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, shutil.copy2, src, dest)


async def exists(path: str) -> bool:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, os.path.exists, path)


async def unlink(path: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, os.unlink, path)


async def rename(old_path: str, new_path: str) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, os.rename, old_path, new_path)


async def mkdir(path: str, options: Optional[dict] = None) -> None:
    loop = asyncio.get_running_loop()
    recursive = options.get('recursive', False) if options else False
    if recursive:
        await loop.run_in_executor(None, lambda: os.makedirs(path, exist_ok=True))
    else:
        await loop.run_in_executor(None, os.mkdir, path)


async def rm(path: str, options: Optional[dict] = None) -> None:
    loop = asyncio.get_running_loop()
    recursive = options.get('recursive', False) if options else False
    force = options.get('force', False) if options else False

    def _rm():
        if recursive:
            if force and not os.path.exists(path):
                return
            shutil.rmtree(path)
        else:
            if force and not os.path.exists(path):
                return
            os.unlink(path)

    await loop.run_in_executor(None, _rm)


async def stat(path: str):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, os.stat, path)
    return _StatResult(result)


class _StatResult:
    def __init__(self, stat_result: os.stat_result):
        self._stat = stat_result
        self.size = stat_result.st_size

    def isFile(self) -> bool:
        import stat as stat_module
        return stat_module.S_ISREG(self._stat.st_mode)

    def isDirectory(self) -> bool:
        import stat as stat_module
        return stat_module.S_ISDIR(self._stat.st_mode)


class WriteStream:
    def __init__(self, path: str):
        self._path = path
        self._file = open(path, 'wb')
        self._on_close = None

    def __del__(self):
        try:
            if not self._file.closed:
                self._file.close()
        except Exception:
            pass

    def write(self, data: Union[str, bytes]) -> None:
        if isinstance(data, str):
            data = data.encode('utf-8')
        self._file.write(data)

    def close(self) -> None:
        self._file.close()
        if self._on_close:
            self._on_close()

    def on(self, event: str, callback) -> None:
        if event == 'close':
            self._on_close = callback

    def pipe_from(self, response) -> None:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                self.write(chunk)
        self.close()


def create_write_stream(path: str) -> WriteStream:
    return WriteStream(path)
