from src.utils.execute_jar import execute_jar
from src.utils.observe_process import observe_process
from src.tools.tool import Tool, ToolVersion


class UberApkSigner(Tool):
    def sign(self, input_paths: list[str], options: dict = None):
        zipalign = (options or {}).get('zipalign', False)
        path_args = []
        for path in input_paths:
            path_args.extend(['--apks', path])

        return observe_process(
            execute_jar(self.jar_path, [
                '--allowResign',
                '--overwrite',
                *([] if zipalign else ['--skipZipAlign']),
                *path_args,
            ]),
            'signing',
        )

    @property
    def name(self) -> str:
        return 'uber-apk-signer'

    @property
    def version(self) -> ToolVersion:
        version_number = '1.3.0'

        return ToolVersion(
            name=f'v{version_number}',
            download_url=
                'https://github.com/patrickfav/uber-apk-signer/releases/download'
                + f'/v{version_number}/uber-apk-signer-{version_number}.jar',
        )
