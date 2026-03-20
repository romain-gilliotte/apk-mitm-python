import asyncio
import glob
import os
from typing import List, Optional, Union


async def _globby_async(patterns: Union[str, List[str]], options: Optional[dict] = None) -> List[str]:
    if isinstance(patterns, str):
        patterns = [patterns]

    loop = asyncio.get_running_loop()
    results = []
    for pattern in patterns:
        matched = await loop.run_in_executor(None, lambda p=pattern: glob.glob(p, recursive=True))
        results.extend(matched)

    results = [path.replace(os.sep, '/') for path in results]
    results.sort()
    return results


async def _globby_stream(patterns: Union[str, List[str]], options: Optional[dict] = None):
    if isinstance(patterns, str):
        patterns = [patterns]

    loop = asyncio.get_running_loop()
    for pattern in patterns:
        matched = await loop.run_in_executor(None, lambda p=pattern: glob.glob(p, recursive=True))
        matched.sort()
        for path in matched:
            yield path.replace(os.sep, '/')


class _Globby:
    async def __call__(self, patterns: Union[str, List[str]], options: Optional[dict] = None) -> List[str]:
        return await _globby_async(patterns, options)

    def stream(self, patterns: Union[str, List[str]], options: Optional[dict] = None):
        return _globby_stream(patterns, options)


globby = _Globby()
