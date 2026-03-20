from apk_mitm.utils import fs
from apk_mitm.dependencies import path as path_utils
from apk_mitm.dependencies.execa import ExecaChildProcess
from apk_mitm.dependencies.rxjs import Observable
from apk_mitm.utils.observe_async import observe_async


def observe_process(
    process: ExecaChildProcess,
    log_name: str,
) -> Observable:
    async def _fn(log):
        await fs.mkdir('logs', {'recursive': True})

        file_name = path_utils.join('logs', f'{log_name}.log')
        failed_file_name = path_utils.join('logs', f'{log_name}.failed.log')
        stream = fs.create_write_stream(file_name)

        process.stdout.on('data', lambda data: (
            log(data.decode('utf-8', errors='replace').strip()),
            stream.write(data),
        ))
        process.stderr.on('data', lambda data: stream.write(data))

        try:
            await process
        except Exception as error:
            await fs.rename(file_name, failed_file_name)
            raise error
        finally:
            stream.close()

    return observe_async(_fn)
