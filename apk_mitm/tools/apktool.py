import re
from dataclasses import dataclass
from typing import Optional

from apk_mitm.dependencies.rxjs import map
from apk_mitm.dependencies.chalk import chalk

from apk_mitm.utils.execute_jar import execute_jar
from apk_mitm.utils.observe_process import observe_process
from apk_mitm.tools.tool import Tool, ToolVersion


@dataclass
class ApktoolOptions:
    framework_path: str
    custom_path: Optional[str] = None


class Apktool(Tool):
    def __init__(self, options: ApktoolOptions):
        super().__init__()
        self._options = options

    def decode(self, input_path: str, output_path: str):
        return self._run(
            [
                'decode',
                input_path,
                '--output',
                output_path,
                '--frame-path',
                self._options.framework_path,
            ],
            'decoding',
        )

    def encode(self, input_path: str, output_path: str, use_aapt2: bool):
        return self._run(
            [
                'build',
                input_path,
                '--output',
                output_path,
                '--frame-path',
                self._options.framework_path,
                *(['--use-aapt2'] if use_aapt2 else []),
            ],
            f"encoding-{'aapt2' if use_aapt2 else 'aapt'}",
        )

    def _run(self, args: list[str], log_name: str):
        return map(lambda line: re.sub(r'I: ', '', line))(
            observe_process(execute_jar(self._path, args), log_name),
        )

    @property
    def _path(self):
        return self._options.custom_path or self.jar_path

    @property
    def name(self) -> str:
        return 'apktool'

    @property
    def version(self) -> ToolVersion:
        if self._options.custom_path:
            return ToolVersion(name=chalk.italic('custom version'))

        version_number = '2.9.3'

        return ToolVersion(
            name=f"v{version_number}",
            download_url=
                'https://github.com/iBotPeaches/Apktool/releases/download'
                + f"/v{version_number}/apktool_{version_number}.jar",
        )
