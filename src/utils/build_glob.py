from src.dependencies import path

# Build a glob pattern that works on POSIX and Windows.
def build_glob(*components: str) -> str:
    # Convert Windows path (using backslashes) to POSIX path (using slashes)
    unix_components = [
        path.posix.sep.join(component.split(path.sep))
        for component in components
    ]

    return path.posix.join(*unix_components)
