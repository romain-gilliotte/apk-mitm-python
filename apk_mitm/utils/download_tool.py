from __future__ import annotations
import sys
from typing import TYPE_CHECKING
from apk_mitm.utils import fs
from apk_mitm.dependencies.path import join
from apk_mitm.dependencies.env_paths import env_paths
from apk_mitm.dependencies.listr import ListrTask, ListrTaskWrapper

if TYPE_CHECKING:
    from apk_mitm.tools.tool import Tool
from apk_mitm.utils.observe_async import observe_async
from apk_mitm.utils.download_file import download_file

cache_path = env_paths('apk-mitm', {'suffix': ''}).cache

def create_tool_download_task(tool: Tool) -> ListrTask:
    def task(_, task: ListrTaskWrapper):
        if not tool.version.download_url:
            return task.skip('Using custom version')

        file_name = f"{tool.name}-{tool.version.name}.jar"
        return download_cached_file(task, tool.version.download_url, file_name)

    return {
        'title': f"Downloading {tool.name} {tool.version.name}",
        'task': task,
    }

def download_cached_file(
    task: ListrTaskWrapper,
    url: str,
    file_name: str,
):
    async def fn(log):
        final_file_path = get_cached_path(file_name)

        if await fs.exists(final_file_path):
            task.skip('Version already downloaded!')
            return

        # Ensure cache directory exists
        await fs.mkdir(cache_path, {'recursive': True})

        # Prevent file corruption by using a temporary file name
        download_file_path = final_file_path + '.dl'
        await download_file(url, download_file_path).for_each(lambda line: (
            # Hide verbose download progress in non-TTY mode
            log(line) if sys.stdout.isatty() else None
        ))
        await fs.rename(download_file_path, final_file_path)

    return observe_async(fn)

def get_cached_path(name: str):
    return join(cache_path, name)
