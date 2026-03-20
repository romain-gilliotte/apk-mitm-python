from src.dependencies.execa import execa

def execute_jar(path: str, args: list[str]):
    return execa('java', ['-jar', path, *args], {
        # Necessary for showing both stdout and stderr in error output
        'all': True,
    })
