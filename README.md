# apk-mitm (Python port)

A Python port of [apk-mitm](https://github.com/niklashigi/apk-mitm), a CLI application that automatically prepares Android APK files for HTTPS inspection.

## What it does

- Decodes the APK using [apktool](https://ibotpeaches.github.io/Apktool/)
- Modifies the `AndroidManifest.xml` to allow user certificates
- Adds/replaces the network security config to trust user CAs
- Disables certificate pinning in Smali code (supports javax, OkHttp 2.x/3.x/4.x)
- Re-encodes and signs the APK with [uber-apk-signer](https://github.com/patrickfav/uber-apk-signer)

Supports `.apk`, `.xapk`, `.apks`, and `.zip` files.

## Upstream sync

This is a **line-by-line port** of the TypeScript original. The goal is to stay as close as possible to the upstream source to make it easy to track changes and keep the port in sync.

- **Upstream repo**: https://github.com/niklashigi/apk-mitm
- **Upstream commit**: [`5a96363`](https://github.com/niklashigi/apk-mitm/commit/5a96363fc9112b97d60fc2bd3799d6bbfd8e4e00)
- The upstream TypeScript source is cloned into `upstream/` (git-ignored) via `scripts/fetch_upstream.sh`

## Requirements

- Python >= 3.13
- Java >= 8
- [uv](https://github.com/astral-sh/uv) (package manager)

## Installation

```bash
git clone https://github.com/eloims/apk-mitm-python.git
cd apk-mitm-python
uv sync
```

## Usage

```bash
uv run apk-mitm-py <path-to-apk>
```

### Options

```
--wait                     Wait for manual changes before re-encoding
--tmp-dir <path>           Where temporary files will be stored
--keep-tmp-dir             Don't delete the temporary directory after patching
--debuggable               Make the patched app debuggable
--skip-patches             Don't apply any patches (for troubleshooting)
--apktool <path-to-jar>    Use custom version of Apktool
--certificate <path>       Add specific certificate to network security config
--maps-api-key <api-key>   Custom Google Maps API key to replace while patching
```

### Example

```bash
uv run apk-mitm-py my-app.apk
# Output: my-app-patched.apk
```

## Project structure

The port mirrors the upstream structure with Python conventions (snake_case filenames):

```
apk_mitm/
├── cli.py                 # CLI entry point
├── index.py               # Public API re-exports
├── patch_apk.py           # APK patching pipeline
├── patch_app_bundle.py    # App bundle (.xapk/.apks) patching
├── dependencies/          # Wrappers around npm deps → Python equivalents
├── tasks/                 # Individual patching tasks
│   └── smali/             # Smali code analysis and patching
├── tools/                 # External tool wrappers (apktool, uber-apk-signer)
└── utils/                 # Shared utilities
```

The `apk_mitm/dependencies/` layer wraps Python libraries to expose the same API as the original npm packages. This keeps the ported application code as close as possible to the TypeScript source.

## License

Same as upstream: [MIT](https://github.com/niklashigi/apk-mitm/blob/main/LICENSE)
