import sys
import platform
import re
import asyncio
import os.path
import importlib.metadata
from typing import TypedDict, Optional, Callable

from src.dependencies import path
from src.utils import fs
from src.dependencies.yargs_parser import parse as parse_args
from src.dependencies.chalk import chalk
from src.dependencies.tempy import tempy

from src.patch_apk import patch_apk, show_app_bundle_warning
from src.patch_app_bundle import patch_xapk_bundle, patch_apks_bundle

from src.tools.apktool import Apktool, ApktoolOptions
from src.tools.uber_apk_signer import UberApkSigner
from src.tools.tool import Tool
from src.utils.user_error import UserError


class TaskOptions(TypedDict, total=False):
    input_path: str
    output_path: str
    skip_patches: bool
    certificate_path: Optional[str]
    maps_api_key: Optional[str]
    apktool: Apktool
    uber_apk_signer: UberApkSigner
    tmp_dir: str
    wait: bool
    is_app_bundle: bool
    debuggable: bool
    skip_decode: bool


try:
    version = importlib.metadata.version("apk-mitm-python")
except importlib.metadata.PackageNotFoundError:
    import tomllib
    _pyproject_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pyproject.toml')
    with open(os.path.normpath(_pyproject_path), 'rb') as _f:
        version = tomllib.load(_f)['project']['version']


async def main():
    args = parse_args(sys.argv[1:], {
        'string': ['apktool', 'certificate', 'tmp-dir', 'maps-api-key'],
        'boolean': ['help', 'skip-patches', 'wait', 'debuggable', 'keep-tmp-dir'],
    })

    if args.help:
        show_help()
        sys.exit()

    input_ = args['_'][0] if len(args['_']) > 0 else None
    if not input_:
        show_help()
        sys.exit(1)
    input_path = path.resolve(input_)

    result = await determine_task(input_path)
    task_function = result['task_function']
    skip_decode = result['skip_decode']
    is_app_bundle = result['is_app_bundle']
    output_name = result['output_name']
    output_path = path.resolve(path.dirname(input_path), output_name)

    # Initialize and validate certificate path
    certificate_path: Optional[str] = None
    maps_api_key: Optional[str] = args['maps-api-key']
    if args.certificate:
        certificate_path = path.resolve(args.certificate)
        certificate_extension = path.extname(certificate_path)

        if certificate_extension != '.pem' and certificate_extension != '.der':
            show_supported_certificate_extensions()

    tmp_dir = path.resolve(args['tmp-dir']) \
        if args['tmp-dir'] \
        else tempy.directory({'prefix': 'apk-mitm-'})
    await fs.mkdir(tmp_dir, {'recursive': True})

    apktool = Apktool(ApktoolOptions(
        framework_path=path.join(tmp_dir, 'framework'),
        custom_path=path.resolve(args.apktool) if args.apktool else None,
    ))
    uber_apk_signer = UberApkSigner()

    show_versions(apktool=apktool, uber_apk_signer=uber_apk_signer)
    if skip_decode:
        print(
            chalk.dim(f'  Patching from decoded apktool directory:\n  {input_path}\n'),
        )
    else:
        print(chalk.dim(f'  Using temporary directory:\n  {tmp_dir}\n'))

    try:
        context = await task_function({
            'input_path': input_path,
            'output_path': output_path,
            'certificate_path': certificate_path,
            'maps_api_key': maps_api_key,
            'tmp_dir': tmp_dir,
            'apktool': apktool,
            'uber_apk_signer': uber_apk_signer,
            'wait': args.wait,
            'skip_patches': args.skipPatches,
            'is_app_bundle': is_app_bundle,
            'debuggable': args.debuggable,
            'skip_decode': skip_decode,
        }).run()

        if task_function == patch_apk and context.get('uses_app_bundle'):
            show_app_bundle_warning()

        print(
            chalk(f'\n  {{green.inverse  Done! }} Patched file: {{bold ./{output_name}}}\n'),
        )

        if not args['keep-tmp-dir']:
            try:
                await fs.rm(tmp_dir, {'recursive': True, 'force': True})
            except Exception as error:
                # No idea why Windows gives us an `EBUSY: resource busy or locked`
                # error here, but deleting the temporary directory isn't the most
                # important thing in the world, so let's just ignore it
                ignore_error = \
                    sys.platform == 'win32' and getattr(error, 'code', None) == 'EBUSY'

                if not ignore_error:
                    raise error

    except Exception as error:
        message = get_error_message(error, tmp_dir=tmp_dir)

        print(
            '\n'.join([
                '',
                chalk('  {red.inverse.bold  Failed! } An error occurred:'),
                '',
                message,
                '',
                '  The full logs of all commands are available here:',
                f'  {path.join(tmp_dir, "logs")}',
                '',
            ]),
            file=sys.stderr,
        )
        if platform.machine().startswith('arm'):
            show_arm_warning()

        sys.exit(1)


async def determine_task(input_path: str):
    file_stats = await fs.stat(input_path)

    output_file_extension = '.apk'

    skip_decode = False
    is_app_bundle = False
    task_function: Callable = None

    if file_stats.isDirectory():
        task_function = patch_apk
        skip_decode = True

        apktool_yaml_path = path.join(input_path, 'apktool.yml')
        if not (await fs.exists(apktool_yaml_path)):
            raise UserError(
                'No "apktool.yml" file found inside the input directory!'
                + ' Make sure to specify a directory created by "apktool decode".',
            )
    else:
        input_file_extension = path.extname(input_path)

        if input_file_extension == '.apk':
            task_function = patch_apk
        elif input_file_extension == '.xapk':
            is_app_bundle = True
            task_function = patch_xapk_bundle
        elif input_file_extension == '.apks' or input_file_extension == '.zip':
            is_app_bundle = True
            task_function = patch_apks_bundle
        else:
            show_supported_extensions()

        output_file_extension = input_file_extension

    base_name = path.basename(input_path, output_file_extension)
    output_name = f'{base_name}-patched{output_file_extension}'

    return {'skip_decode': skip_decode, 'task_function': task_function, 'is_app_bundle': is_app_bundle, 'output_name': output_name}


def get_error_message(error, tmp_dir: str):
    # User errors can be shown without a stack trace
    if isinstance(error, UserError):
        return str(error)

    # Errors from commands can also be shown without a stack trace
    if getattr(error, 'all', None):
        return format_command_error(error.all, tmp_dir=tmp_dir)

    import traceback
    return ''.join(traceback.format_exception(type(error), error, error.__traceback__))


def format_command_error(error: str, tmp_dir: str):
    result = error
    # Replace mentions of the (sometimes very long) temporary directory path
    result = result.replace(tmp_dir, chalk('{bold <tmp_dir>}'))
    # Highlight (usually relevant) warning lines in Apktool output
    result = re.sub(r'^W: .+$', lambda m: chalk(f'{{yellow {m.group(0)}}}'), result, flags=re.MULTILINE)
    # De-emphasize Apktool info lines
    result = re.sub(r'^I: .+$', lambda m: chalk(f'{{dim {m.group(0)}}}'), result, flags=re.MULTILINE)
    # De-emphasize (not very helpful) Apktool "could not exec" error message
    result = re.sub(
        r'^.+brut\.common\.BrutException: could not exec.+$',
        lambda m: chalk(f'{{dim {m.group(0)}}}'),
        result,
        flags=re.MULTILINE,
    )
    return result


def show_help():
    print(chalk("""
  $ {bold apk-mitm} <path-to-apk/xapk/apks/decoded-directory>

  {blue {dim.bold *} Optional flags:}
  {dim {bold --wait} Wait for manual changes before re-encoding}
  {dim {bold --tmp-dir <path>} Where temporary files will be stored}
  {dim {bold --keep-tmp-dir} Don't delete the temporary directory after patching}
  {dim {bold --debuggable} Make the patched app debuggable}
  {dim {bold --skip-patches} Don't apply any patches (for troubleshooting)}
  {dim {bold --apktool <path-to-jar>} Use custom version of Apktool}
  {dim {bold --certificate <path-to-pem/der>} Add specific certificate to network security config}
  {dim {bold --maps-api-key <api-key>} Add custom Google Maps API key to be replaced while patching apk}
  """))


def show_supported_extensions():
    print(chalk("""{yellow
  It looks like you tried running {bold apk-mitm} with an unsupported file type!

  Only the following file extensions are supported: {bold .apk}, {bold .xapk}, and {bold .apks} (or {bold .zip})
  }"""))

    sys.exit(1)


def show_supported_certificate_extensions():
    print(chalk("""{yellow
  It looks like the certificate file you provided is unsupported!

  Only {bold .pem} and {bold .der} certificate files are supported.
  }"""))

    sys.exit(1)


def show_versions(apktool: Tool, uber_apk_signer: Tool):
    print(chalk(f"""
  {{dim \u256d}} {{blue {{bold apk-mitm}} v{version}}}
  {{dim \u251c {{bold apktool}} {apktool.version.name}
  \u2570 {{bold uber-apk-signer}} {uber_apk_signer.version.name}}}
  """))


def show_arm_warning():
    print(chalk("""{yellow
  {inverse.bold  NOTE }

  {bold apk-mitm} doesn't officially support ARM-based devices (like Raspberry Pi's)
  at the moment, so the error above might be a result of that. Please try
  patching this APK on a device with a more common CPU architecture like x64
  before reporting an issue.
  }"""))


asyncio.run(main())
