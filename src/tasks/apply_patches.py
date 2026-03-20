from src.dependencies.path import join
from src.dependencies.listr import Listr

from src.tasks.modify_manifest import modify_manifest
from src.tasks.create_netsec_config import create_network_security_config
from src.tasks.disable_certificate_pinning import disable_certificate_pinning
from src.tasks.copy_certificate_file import copy_certificate_file


def apply_patches(
    decode_dir: str,
    debuggable: bool = False,
    certificate_path: str = None,
    maps_api_key: str = None,
):
    return Listr([
        {
            "title": "Modifying app manifest",
            "task": lambda context, _task: _modify_manifest_task(
                context, decode_dir, debuggable, maps_api_key,
            ),
        },
        {
            "title": "Copying certificate file",
            "skip": lambda *args: False if certificate_path else "--certificate flag not specified.",
            "task": lambda _context, _task: copy_certificate_file(decode_dir, certificate_path),
        },
        {
            "title": "Replacing network security config",
            "task": lambda _context, _task: create_network_security_config(
                join(decode_dir, "res/xml/nsc_mitm.xml"),
                certificate_path=certificate_path,
            ),
        },
        {
            "title": "Disabling certificate pinning",
            "task": lambda _context, task: disable_certificate_pinning(decode_dir, task),
        },
    ])


async def _modify_manifest_task(context, decode_dir, debuggable, maps_api_key):
    result = await modify_manifest(
        join(decode_dir, "AndroidManifest.xml"),
        debuggable,
        maps_api_key,
    )

    context["uses_app_bundle"] = result["usesAppBundle"]
