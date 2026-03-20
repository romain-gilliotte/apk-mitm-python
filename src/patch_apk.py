import sys
import asyncio

from src.dependencies import path
from src.utils import fs
from src.dependencies.listr import Listr
from src.dependencies.chalk import chalk

from src.utils.observe_async import observe_async
from src.tasks.apply_patches import apply_patches
from src.tasks.check_prerequisites import check_prerequisites


def patch_apk(options):
    apktool = options["apktool"]
    uber_apk_signer = options["uber_apk_signer"]

    decode_dir = options["input_path"] if options.get("skip_decode") \
        else path.join(options["tmp_dir"], "decode")
    tmp_apk_path = path.join(options["tmp_dir"], "tmp.apk")

    fall_back_to_aapt = [False]

    return Listr([
        {
            "title": "Checking prerequisities",
            "task": lambda _ctx=None, _task=None: check_prerequisites(options),
        },
        {
            "title": "Decoding APK file",
            "skip": lambda *args: options.get("skip_decode"),
            "task": lambda _ctx=None, _task=None: apktool.decode(options["input_path"], decode_dir),
        },
        {
            "title": "Applying patches",
            "skip": lambda *args: options.get("skip_patches"),
            "task": lambda _ctx=None, _task=None: apply_patches(
                decode_dir,
                debuggable=options.get("debuggable"),
                certificate_path=options.get("certificate_path"),
                maps_api_key=options.get("maps_api_key"),
            ),
        },
        {
            "title": "Waiting for you to make changes",
            "enabled": lambda _ctx=None: options.get("wait"),
            "task": lambda _ctx=None, _task=None: observe_async(
                lambda log: _wait_for_keypress(log)
            ),
        },
        {
            "title": "Encoding patched APK file",
            "task": lambda _ctx=None, _task=None: Listr([
                {
                    "title": "Encoding using AAPT2",
                    "task": lambda _ctx2, task: observe_async(
                        lambda next: _encode_aapt2(next, apktool, decode_dir, tmp_apk_path, task, fall_back_to_aapt)
                    ),
                },
                {
                    "title": chalk("Encoding using AAPT {dim [fallback]}"),
                    "skip": lambda *args: not fall_back_to_aapt[0],
                    "task": lambda _ctx2=None, _task2=None: apktool.encode(decode_dir, tmp_apk_path, False),
                },
            ]),
        },
        {
            "title": "Signing patched APK file",
            "task": lambda _ctx=None, _task=None: observe_async(
                lambda log: _sign_apk(log, uber_apk_signer, tmp_apk_path, options)
            ),
        },
    ])


async def _wait_for_keypress(log):
    sys.stdin.reconfigure(encoding="utf-8")

    log("Press any key to continue.")
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, sys.stdin.read, 1)


async def _encode_aapt2(next, apktool, decode_dir, tmp_apk_path, task, fall_back_to_aapt):
    try:
        await apktool \
            .encode(decode_dir, tmp_apk_path, True) \
            .for_each(next)
    except Exception:
        task.skip("Failed, falling back to AAPT...")
        fall_back_to_aapt[0] = True


async def _sign_apk(log, uber_apk_signer, tmp_apk_path, options):
    await uber_apk_signer \
        .sign([tmp_apk_path], {"zipalign": True}) \
        .for_each(lambda line: log(line))

    await fs.copy_file(tmp_apk_path, options["output_path"])


def show_app_bundle_warning():
    print(chalk("""{yellow
  {inverse.bold  WARNING }

  This app seems to be using {bold Android App Bundle} which means that you
  will likely run into problems installing it. That's because this app
  is made out of {bold multiple APK files} and you've only got one of them.

  If you want to patch an app like this with {bold apk-mitm}, you'll have to
  supply it with all the APKs. You have two options for doing this:

  \u2013 download a {bold *.xapk} file {dim (for example from https://apkpure.com\u200b)}
  \u2013 export a {bold *.apks} file {dim (using https://github.com/Aefyr/SAI\u200b)}

  You can then run {bold apk-mitm} again with that file to patch the bundle.}"""))
