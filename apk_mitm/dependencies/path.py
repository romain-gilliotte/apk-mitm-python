import os
import os.path
import posixpath


def resolve(*paths: str) -> str:
    if not paths:
        return os.getcwd()
    result = os.path.join(os.getcwd(), *paths)
    return os.path.normpath(result)


def join(*paths: str) -> str:
    return os.path.join(*paths)


def dirname(p: str) -> str:
    return os.path.dirname(p)


def basename(p: str, ext: str = "") -> str:
    name = os.path.basename(p)
    if ext and name.endswith(ext):
        name = name[: -len(ext)]
    return name


def extname(p: str) -> str:
    _, ext = os.path.splitext(p)
    return ext


sep = os.sep


class _Posix:
    sep = "/"

    @staticmethod
    def join(*paths: str) -> str:
        return posixpath.join(*paths)


posix = _Posix()
