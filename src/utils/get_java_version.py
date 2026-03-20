import re

from src.dependencies.execa import execa, ExecaError
from src.utils.user_error import UserError

# Returns the major version of the system's default Java installation.
async def get_java_version():
    try:
        result = await execa('java', ['-version'])
        stderr = result.stderr
        match = JAVA_VERSION_PATTERN.search(stderr)
        major_version_string = match.group('major') if match else None
        if not major_version_string:
            message = f'Could not extract Java major version from "java -version" output!\n{stderr}'
            raise UserError(message)

        return int(major_version_string)
    except ExecaError as error:
        if error.code == 'ENOENT':
            raise UserError(
                'No "java" executable could be found!'
                + ' Make sure that Java is installed and available in your PATH.'
            )

        raise

# Pattern for extracting the Java major version from the output of
# `java -version` (stripping the `1.` prefix from versions prior to Java 9).
#
# Some example outputs with their respective versions:
# - `openjdk version "1.8.0_292"` -> `8`
# - `openjdk version "11.0.11" 2021-04-20` -> `11`
# - `java version "15" 2020-09-15` -> `15`
JAVA_VERSION_PATTERN = re.compile(r'"(?:1\.)?(?P<major>\d+).*?"')
