from apk_mitm.utils import fs
from apk_mitm.dependencies import path

# Copies the certificate file at `source_path` to the correct location within
# the APK's `decode_dir`, so it can then be referenced in the Network Security
# Config.
async def copy_certificate_file(
    decode_dir: str,
    source_path: str,
):
    raw_dir = path.join(decode_dir, 'res/raw/')
    await fs.mkdir(raw_dir, {'recursive': True})

    destination_path = path.join(raw_dir, path.basename(source_path))
    await fs.copy_file(source_path, destination_path)
