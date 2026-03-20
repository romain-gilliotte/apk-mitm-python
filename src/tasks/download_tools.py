from __future__ import annotations
from typing import TYPE_CHECKING

from src.dependencies.listr import Listr

from src.utils.download_tool import create_tool_download_task

if TYPE_CHECKING:
    from src.cli import TaskOptions

def download_tools(options: TaskOptions):
    return Listr(
        [create_tool_download_task(options['apktool']), create_tool_download_task(options['uber_apk_signer'])],
        {'concurrent': True},
    )
