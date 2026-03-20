import os
import sys
import tempfile
from pathlib import Path


class _EnvPaths:
    def __init__(self, name):
        homedir = Path.home()

        if sys.platform == 'darwin':
            library = homedir / 'Library'
            self.data = str(library / 'Application Support' / name)
            self.config = str(library / 'Preferences' / name)
            self.cache = str(library / 'Caches' / name)
            self.log = str(library / 'Logs' / name)
            self.temp = str(Path(tempfile.gettempdir()) / name)
        elif sys.platform == 'win32':
            app_data = os.environ.get('APPDATA', str(homedir / 'AppData' / 'Roaming'))
            local_app_data = os.environ.get('LOCALAPPDATA', str(homedir / 'AppData' / 'Local'))
            self.data = str(Path(local_app_data) / name / 'Data')
            self.config = str(Path(app_data) / name / 'Config')
            self.cache = str(Path(local_app_data) / name / 'Cache')
            self.log = str(Path(local_app_data) / name / 'Log')
            self.temp = str(Path(tempfile.gettempdir()) / name)
        else:
            username = homedir.name
            self.data = str(Path(os.environ.get('XDG_DATA_HOME', str(homedir / '.local' / 'share'))) / name)
            self.config = str(Path(os.environ.get('XDG_CONFIG_HOME', str(homedir / '.config'))) / name)
            self.cache = str(Path(os.environ.get('XDG_CACHE_HOME', str(homedir / '.cache'))) / name)
            # https://wiki.debian.org/XDGBaseDirectorySpecification#state
            self.log = str(Path(os.environ.get('XDG_STATE_HOME', str(homedir / '.local' / 'state'))) / name)
            self.temp = str(Path(tempfile.gettempdir()) / username / name)


def env_paths(name, options=None):
    if not isinstance(name, str):
        raise TypeError(f'Expected string, got {type(name).__name__}')

    if options is None:
        options = {}

    suffix = options.get('suffix', 'nodejs')

    if suffix:
        # Add suffix to prevent possible conflict with native apps
        name += f'-{suffix}'

    return _EnvPaths(name)
