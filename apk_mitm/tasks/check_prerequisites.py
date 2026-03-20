from __future__ import annotations
import sys
from typing import TYPE_CHECKING

from apk_mitm.dependencies.execa import execa
from apk_mitm.dependencies.listr import Listr

if TYPE_CHECKING:
    from apk_mitm.cli import TaskOptions
from apk_mitm.utils.get_java_version import get_java_version
from apk_mitm.utils.user_error import UserError
from apk_mitm.tasks.download_tools import download_tools

MIN_PYTHON_VERSION = 3
MIN_JAVA_VERSION = 8

def check_prerequisites(options: TaskOptions):
    return Listr([
        {
            'title': 'Checking Python version',
            'task': lambda ctx=None, task=None: _check_python_version(),
        },
        {
            'title': 'Checking Java version',
            'task': lambda ctx=None, task=None: _check_java_version(),
        },
        {
            'title': 'Checking additional tools',
            'task': lambda ctx=None, task=None: _check_additional_tools(options),
        },
        {
            'title': 'Downloading tools',
            'task': lambda ctx=None, task=None: download_tools(options),
        },
    ])

def _check_python_version():
    major_version = sys.version_info[0]
    if major_version < MIN_PYTHON_VERSION:
        raise VersionError('Python', MIN_PYTHON_VERSION, major_version)

async def _check_java_version():
    major_version = await get_java_version()
    if major_version < MIN_JAVA_VERSION:
        raise VersionError('Java', MIN_JAVA_VERSION, major_version)

async def _check_additional_tools(options):
    if options['is_app_bundle'] and sys.platform != 'win32':
        await ensure_zip_ulities_available()

# Ensure that `zip` and `unzip` are installed on Linux or macOS. Both are used
# (through the `cross-zip` package) when patching App Bundles.
async def ensure_zip_ulities_available():
    try:
        await execa('unzip', ['-v'])
        await execa('zip', ['-v'])
    except Exception:
        raise UserError(
            'apk-mitm requires the commands "unzip" and "zip" to be installed when patching App Bundles.'
            + " Make sure they're both installed and try again!",
        )

class VersionError(UserError):
    def __init__(self, tool: str, min_version: int, current_version: int):
        super().__init__(
            f'apk-mitm requires at least {tool} {min_version} to work and you seem to be using {tool} {current_version}.'
            + f' Please upgrade your {tool} installation and try again!',
        )
        self.name = VersionError.__name__
