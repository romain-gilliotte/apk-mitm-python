import asyncio
import subprocess


class ExecaError(Exception):
    def __init__(self, stdout, stderr, exit_code, command, all_output=None, code=None):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.exitCode = exit_code
        self.command = command
        self.failed = True
        self.killed = False
        self.timedOut = False
        self.isCanceled = False
        self.all = all_output
        self.code = code
        message = f"Command failed with exit code {exit_code}: {command}"
        if stderr:
            message += f"\n{stderr}"
        if stdout:
            message += f"\n{stdout}"
        super().__init__(message)
        self.shortMessage = f"Command failed with exit code {exit_code}: {command}"


class ExecaReturnValue:
    def __init__(self, stdout, stderr, exit_code, command, all_output=None):
        self.stdout = stdout
        self.stderr = stderr
        self.exitCode = exit_code
        self.command = command
        self.failed = False
        self.killed = False
        self.timedOut = False
        self.isCanceled = False
        self.all = all_output


class _StreamAdapter:
    def __init__(self):
        self._stream = None
        self._listeners = {}

    def _set_stream(self, stream):
        self._stream = stream

    def on(self, event, callback):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        return self

    async def _read_loop(self):
        if self._stream is None:
            return
        try:
            while True:
                data = await self._stream.read(4096)
                if not data:
                    break
                if 'data' in self._listeners:
                    for cb in self._listeners['data']:
                        cb(data)
        except Exception:
            pass


class ExecaChildProcess:
    def __init__(self, file, args=None, options=None):
        self._file = file
        self._args = args or []
        self._options = options or {}
        self._process = None
        self._started = False
        self.stdout = _StreamAdapter()
        self.stderr = _StreamAdapter()
        self.all = _StreamAdapter() if self._options.get('all') else None
        self.killed = False

    async def _start(self):
        if self._started:
            return
        self._started = True
        try:
            self._process = await asyncio.create_subprocess_exec(
                self._file, *self._args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            error = ExecaError('', '', None, self._command_string, code='ENOENT')
            raise error

        self.stdout._set_stream(self._process.stdout)
        self.stderr._set_stream(self._process.stderr)

    @property
    def _command_string(self):
        parts = [self._file] + self._args
        return ' '.join(parts)

    async def _wait(self):
        await self._start()

        use_all = self._options.get('all', False)

        stdout_chunks = []
        stderr_chunks = []
        all_chunks = []

        def capture_stdout(data):
            stdout_chunks.append(data)
            if use_all:
                all_chunks.append(data)

        def capture_stderr(data):
            stderr_chunks.append(data)
            if use_all:
                all_chunks.append(data)

        self.stdout._listeners.setdefault('data', []).append(capture_stdout)
        self.stderr._listeners.setdefault('data', []).append(capture_stderr)

        await asyncio.gather(
            self.stdout._read_loop(),
            self.stderr._read_loop(),
        )
        await self._process.wait()

        self.stdout._listeners.get('data', []).remove(capture_stdout)
        self.stderr._listeners.get('data', []).remove(capture_stderr)

        stdout_str = b''.join(stdout_chunks).decode('utf-8', errors='replace')
        stderr_str = b''.join(stderr_chunks).decode('utf-8', errors='replace')
        all_str = b''.join(all_chunks).decode('utf-8', errors='replace') if use_all else None

        if stdout_str.endswith('\n'):
            stdout_str = stdout_str[:-1]
        if stderr_str.endswith('\n'):
            stderr_str = stderr_str[:-1]
        if all_str is not None and all_str.endswith('\n'):
            all_str = all_str[:-1]

        exit_code = self._process.returncode

        if exit_code != 0:
            error = ExecaError(stdout_str, stderr_str, exit_code, self._command_string, all_str)
            error.killed = self.killed
            raise error

        result = ExecaReturnValue(stdout_str, stderr_str, exit_code, self._command_string, all_str)
        return result

    def kill(self, signal=None):
        if self._process:
            self.killed = True
            if signal:
                self._process.send_signal(signal)
            else:
                self._process.terminate()

    def __await__(self):
        return self._wait().__await__()


def execa(file, args=None, options=None):
    return ExecaChildProcess(file, args, options)
