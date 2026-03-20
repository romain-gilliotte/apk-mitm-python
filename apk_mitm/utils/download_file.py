from apk_mitm.utils import fs
from apk_mitm.dependencies.rxjs import Observable
from apk_mitm.dependencies.follow_redirects import https


def download_file(url: str, path: str):
    def subscribe(subscriber):
        def on_response(response):
            if response.statusCode != 200:
                error = Exception(
                    f'The URL "{url}" returned status code {response.statusCode}, expected 200.',
                )

                # Cancel download with error
                response.destroy(error)

            file_stream = fs.create_write_stream(path)

            total_length = int(response.headers['content-length'])
            current_length = 0

            def report_progress():
                nonlocal current_length
                percentage = current_length / total_length
                subscriber.next(
                    f'{(percentage * 100):.2f}% done ({format_bytes(current_length)} / {format_bytes(total_length)} MB)',
                )
            report_progress()

            response.pipe(file_stream)

            def on_data(chunk):
                nonlocal current_length
                current_length += chunk.byteLength
                report_progress()
            response.on('data', on_data)
            response.on('error', lambda error: subscriber.error(error))

            file_stream.on('close', lambda: subscriber.complete())

        https \
            .get(url, on_response) \
            .on('error', lambda error: subscriber.error(error))

    return Observable(subscribe)


def format_bytes(bytes: int):
    return f'{(bytes / 1000000):.2f}'
