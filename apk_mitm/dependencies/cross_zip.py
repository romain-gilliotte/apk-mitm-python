import asyncio
import os
import zipfile


async def unzip(zip_path: str, output_dir: str) -> None:
    def _unzip():
        os.makedirs(os.path.dirname(output_dir), exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(output_dir)

    await asyncio.get_running_loop().run_in_executor(None, _unzip)


async def zip(input_dir: str, output_path: str, include_base_directory: bool = False) -> int:
    def _zip():
        if os.path.exists(output_path):
            os.remove(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if include_base_directory:
                base = os.path.basename(input_dir)
                for root, dirs, files in os.walk(input_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.join(base, os.path.relpath(file_path, input_dir))
                        zf.write(file_path, arcname)
            else:
                for root, dirs, files in os.walk(input_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, input_dir)
                        zf.write(file_path, arcname)

        return os.stat(output_path).st_size

    return await asyncio.get_running_loop().run_in_executor(None, _zip)
