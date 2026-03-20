from apk_mitm.dependencies.globby import globby
from apk_mitm.dependencies.listr import ListrTaskWrapper

from apk_mitm.utils.observe_async import observe_async
from apk_mitm.tasks.smali.process_file import process_smali_file
from apk_mitm.utils.build_glob import build_glob


async def disable_certificate_pinning(
    directory_path: str,
    task: ListrTaskWrapper,
):
    async def fn(log):
        smali_glob = build_glob(directory_path, 'smali*/**/*.smali')

        pinning_found = False

        log('Scanning Smali files...')
        async for file_path_chunk in globby.stream(smali_glob):
            # Required because Node.js streams are not typed as generics
            file_path = file_path_chunk

            had_pinning = await process_smali_file(file_path, log)
            if had_pinning:
                pinning_found = True

        if not pinning_found:
            task.skip('No certificate pinning logic found.')

    return observe_async(fn)
