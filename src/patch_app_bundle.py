import json
import platform

from src.dependencies.cross_zip import unzip, zip
from src.utils import fs
from src.dependencies import path
from src.dependencies.globby import globby
from src.dependencies.listr import Listr
from src.dependencies.execa import execa

from src.patch_apk import patch_apk
from src.utils.observe_async import observe_async
from src.utils.build_glob import build_glob


def patch_xapk_bundle(options):
    return patch_app_bundle(options, is_xapk=True)


def patch_apks_bundle(options):
    return patch_app_bundle(options, is_xapk=False)


def patch_app_bundle(options, is_xapk):
    input_path = options["input_path"]
    output_path = options["output_path"]
    tmp_dir = options["tmp_dir"]
    uber_apk_signer = options["uber_apk_signer"]

    bundle_dir = path.join(tmp_dir, 'bundle')
    base_apk_path = [path.join(bundle_dir, 'base.apk')]

    async def extract_apks():
        await unzip(input_path, bundle_dir)

        if platform.system() != 'Windows':
            # Under Unix: Make sure the user has read and write permissions to
            # the extracted files (which is sometimes not the case by default)
            await execa('chmod', ['-R', 'u+rw', bundle_dir])

    async def find_base_apk_path():
        manifest_path = path.join(bundle_dir, 'manifest.json')
        manifest_content = await fs.read_file(manifest_path, 'utf-8')
        manifest = json.loads(manifest_content)

        base_apk_path[0] = path.join(bundle_dir, get_xapk_base_name(manifest))

    tasks = [
        {
            'title': 'Extracting APKs',
            'task': lambda _ctx=None, _task=None: extract_apks(),
        },
    ]

    if is_xapk:
        tasks.append({
            'title': 'Finding base APK path',
            'task': lambda _ctx=None, _task=None: find_base_apk_path(),
        })

    tasks.append({
        'title': 'Patching base APK',
        'task': lambda _ctx=None, _task=None: patch_apk({
            **options,
            'input_path': base_apk_path[0],
            'output_path': base_apk_path[0],
            'tmp_dir': path.join(tmp_dir, 'base-apk'),
        }),
    })

    tasks.append({
        'title': 'Signing APKs',
        'task': lambda _ctx=None, _task=None: observe_async(
            lambda log: _sign_apks(log, bundle_dir, uber_apk_signer)
        ),
    })

    tasks.append({
        'title': 'Compressing APKs',
        'task': lambda _ctx=None, _task=None: zip(bundle_dir, output_path),
    })

    return Listr(tasks)


async def _sign_apks(log, bundle_dir, uber_apk_signer):
    apk_files = await globby(build_glob(bundle_dir, '**/*.apk'))

    await uber_apk_signer \
        .sign(apk_files, {'zipalign': False}) \
        .for_each(lambda line: log(line))


def get_xapk_base_name(manifest):
    if manifest.get('split_apks'):
        return [apk for apk in manifest['split_apks'] if apk['id'] == 'base'][0]['file']

    return f"{manifest['package_name']}.apk"
