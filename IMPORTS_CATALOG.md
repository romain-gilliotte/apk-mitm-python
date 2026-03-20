# Catalogue des imports externes — apk-mitm

Généré par scan de `upstream/src/` pour servir d'entrée à la Phase 2 (création de `src/dependencies/`).

## Imports par package

### chalk
- **Members**: default → `chalk.red()`, `.green()`, `.yellow()`, `.bold()`, `.dim()`, `.inverse()`, `.italic()`, template literals
- **Imported by**: cli.ts, patch-apk.ts, tasks/smali/process-file.ts, tools/apktool.ts, utils/observe-listr.ts

### yargs-parser
- **Members**: default → `parseArgs(args, options)`
- **Imported by**: cli.ts

### listr
- **Members**: `Listr` (default, class), `ListrTask`, `ListrTaskWrapper`, `ListrTaskObject`, `ListrRenderer`
- **Imported by**: cli.ts, patch-apk.ts, patch-app-bundle.ts, tasks/apply-patches.ts, tasks/check-prerequisites.ts, tasks/download-tools.ts, utils/download-tool.ts, utils/observe-listr.ts

### tempy
- **Members**: `tempy.directory()`
- **Imported by**: cli.ts

### path (Node built-in)
- **Members**: `resolve`, `dirname`, `join`, `extname`, `basename`, `sep`, `posix.sep`, `posix.join`
- **Imported by**: cli.ts, patch-apk.ts, patch-app-bundle.ts, tasks/apply-patches.ts, tasks/copy-certificate-file.ts, tasks/create-netsec-config.ts, utils/build-glob.ts, utils/download-tool.ts, utils/observe-process.ts

### fs (Node built-in)
- **Members**: `createWriteStream`, `readFile`, `writeFile`, `copyFile`, `exists`, `unlink`, `rename`, `mkdir`, `rm`, `stat` (wrappé via `src/utils/fs.ts` + `fs/promises`)
- **Imported by**: utils/fs.ts (puis réexporté vers quasi tous les fichiers)

### util (Node built-in)
- **Members**: `promisify`
- **Imported by**: utils/fs.ts

### events (Node built-in)
- **Members**: `once`
- **Imported by**: patch-apk.ts

### os (Node built-in)
- **Members**: `type()`
- **Imported by**: patch-app-bundle.ts, tasks/smali/process-file.ts

### @tybys/cross-zip
- **Members**: `unzip`, `zip`
- **Imported by**: patch-app-bundle.ts

### globby
- **Members**: `globby()`, `globby.stream()`
- **Imported by**: patch-app-bundle.ts, tasks/disable-certificate-pinning.ts

### execa
- **Members**: `execa()` (function), `ExecaChildProcess` (type)
- **Imported by**: patch-app-bundle.ts, tasks/check-prerequisites.ts, utils/execute-jar.ts, utils/get-java-version.ts

### xml-js
- **Members**: `xml2js()`, `js2xml()`, `Element` (type)
- **Imported by**: tasks/modify-manifest.ts

### rxjs
- **Members**: `Observable`, `Subject`, `Subscriber`
- **Imported by**: utils/download-file.ts, utils/observe-async.ts, utils/observe-listr.ts, utils/observe-process.ts

### rxjs/operators
- **Members**: `map`
- **Imported by**: tools/apktool.ts

### follow-redirects
- **Members**: `https.get()`
- **Imported by**: utils/download-file.ts

### escape-string-regexp
- **Members**: `escapeStringRegexp()` (default)
- **Imported by**: tasks/smali/process-file.ts

### env-paths
- **Members**: `envPaths(name)` → `.cache`
- **Imported by**: utils/download-tool.ts

## Correspondance avec `src/dependencies/`

| Fichier dependency | Package(s) couverts | API à exposer |
|---|---|---|
| `chalk.py` | chalk | `chalk` object avec `.red()`, `.green()`, `.yellow()`, `.bold()`, `.dim()`, `.inverse()`, `.italic()`, template tag |
| `yargs_parser.py` | yargs-parser | `parse(args, options)` |
| `listr.py` | listr | `Listr`, `ListrTask`, `ListrTaskWrapper`, `ListrTaskObject`, `ListrRenderer` |
| `rxjs.py` | rxjs, rxjs/operators | `Observable`, `Subject`, `Subscriber`, `map` |
| `execa.py` | execa | `execa()`, `ExecaChildProcess` |
| `globby.py` | globby | `globby()`, `globby.stream()` |
| `xml_js.py` | xml-js | `xml2js()`, `js2xml()`, `Element` |
| `follow_redirects.py` | follow-redirects | `https.get()` |
| `tempy.py` | tempy | `tempy.directory()` |
| `escape_string_regexp.py` | escape-string-regexp | `escape_string_regexp()` |
| `cross_zip.py` | @tybys/cross-zip | `unzip()`, `zip()` |
| `env_paths.py` | env-paths | `env_paths(name)` |
| `fs.py` | fs (Node built-in) + util.promisify | `read_file`, `write_file`, `readdir`, `exists`, `mkdir`, `copy_file`, `stat`, `create_write_stream`, `unlink`, `rename`, `rm` |
| `path.py` | path (Node built-in) | `resolve`, `join`, `dirname`, `basename`, `extname`, `sep`, `posix` |

## Notes

- `events.once` → géré inline avec `asyncio` dans le code porté
- `os.type()` → géré inline avec `platform.system()` dans le code porté
- `util.promisify` → pas nécessaire en Python (pas de callback pattern)
