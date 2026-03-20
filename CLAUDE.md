# apk-mitm-python

## Objectif

Port ligne à ligne du repo TypeScript [apk-mitm](https://github.com/niklashigi/apk-mitm) (branche `main`) en Python.

## Regles strictes

- **Porter le code ligne à ligne** : chaque fichier TypeScript doit etre traduit fidèlement en Python.
- **Ne pas improviser** : ne pas inventer de logique, de fonctions, ou de comportements qui n'existent pas dans le code source TypeScript.
- **Ne pas améliorer** : ne pas refactorer, ne pas optimiser, ne pas moderniser. Reproduire exactement la logique existante.
- **Ne pas ajouter** : pas de docstrings, pas de commentaires supplémentaires, pas de type hints supplémentaires sauf ceux qui correspondent aux types TypeScript.
- **Ne pas supprimer** : si le code TypeScript a un commentaire, le garder. Si il a une logique qui semble inutile, la garder.

## Correspondance de structure

```
TypeScript (source)              Python (cible)
─────────────────────────────    ──────────────────────────────────
src/cli.ts                   →  src/cli.py
src/index.ts                 →  src/index.py
src/patch_apk.ts             →  src/patch_apk.py
src/patch_app_bundle.ts      →  src/patch_app_bundle.py
src/tasks/apply_patches.ts   →  src/tasks/apply_patches.py
src/tasks/check_prerequisites.ts → src/tasks/check_prerequisites.py
src/tasks/copy_certificate_file.ts → src/tasks/copy_certificate_file.py
src/tasks/create_netsec_config.ts → src/tasks/create_netsec_config.py
src/tasks/disable_certificate_pinning.ts → src/tasks/disable_certificate_pinning.py
src/tasks/download_tools.ts  →  src/tasks/download_tools.py
src/tasks/modify_manifest.ts →  src/tasks/modify_manifest.py
src/tasks/smali/parse_head.ts → src/tasks/smali/parse_head.py
src/tasks/smali/patches.ts   →  src/tasks/smali/patches.py
src/tasks/smali/process_file.ts → src/tasks/smali/process_file.py
src/tasks/smali/types.ts     →  src/tasks/smali/types.py
src/tools/apktool.ts         →  src/tools/apktool.py
src/tools/tool.ts            →  src/tools/tool.py
src/tools/uber_apk_signer.ts →  src/tools/uber_apk_signer.py
src/utils/build_glob.ts      →  src/utils/build_glob.py
src/utils/download_file.ts   →  src/utils/download_file.py
src/utils/download_tool.ts   →  src/utils/download_tool.py
src/utils/execute_jar.ts     →  src/utils/execute_jar.py
src/utils/fs.ts              →  src/utils/fs.py
src/utils/get_java_version.ts → src/utils/get_java_version.py
src/utils/observe_async.ts   →  src/utils/observe_async.py
src/utils/observe_listr.ts   →  src/utils/observe_listr.py
src/utils/observe_process.ts →  src/utils/observe_process.py
src/utils/user_error.ts      →  src/utils/user_error.py
```

Les noms de fichiers passent de camelCase/kebab-case à snake_case (convention Python).

## Couche de dépendances : `src/dependencies/`

Les dépendances TypeScript sont encapsulées dans `src/dependencies/`, un fichier par dépendance. Chaque fichier expose **la même interface** que le module TypeScript original (mêmes noms de fonctions/classes, mêmes signatures). L'implémentation interne utilise des libs Python, mais le code appelant n'a pas besoin de le savoir.

Cela permet au code porté de rester le plus proche possible de l'original : au lieu de réécrire les appels, on importe depuis `src.dependencies.<module>`.

```
src/dependencies/
├── __init__.py
├── chalk.py              # expose chalk.red(), chalk.green(), etc. → colorama en interne
├── yargs_parser.py       # expose parse(args) → argparse en interne
├── listr.py              # expose Listr(tasks).run() → implem séquentielle custom
├── rxjs.py               # expose Observable, Subject, etc. → implem minimale custom
├── execa.py              # expose execa(cmd, args) → subprocess en interne
├── globby.py             # expose globby(patterns) → glob/pathlib en interne
├── xml_js.py             # expose xml2js(), js2xml() → xml.etree en interne
├── follow_redirects.py   # expose https.get() → requests/urllib en interne
├── tempy.py              # expose temporaryFile(), temporaryDirectory() → tempfile en interne
├── escape_string_regexp.py # expose escapeStringRegexp() → re.escape en interne
├── cross_zip.py          # expose zip(), unzip() → zipfile en interne
├── env_paths.py          # expose envPaths(name) → platformdirs en interne
├── fs.py                 # expose readFile, writeFile, etc. → os/pathlib/shutil en interne
├── path.py               # expose join, resolve, basename, etc. → os.path/pathlib en interne
```

### Règle pour le code porté

Quand le code TypeScript fait :
```typescript
import chalk from 'chalk'
```
Le code Python fait :
```python
from src.dependencies.chalk import chalk
```

L'interface exposée par chaque fichier dans `src/dependencies/` doit correspondre exactement à ce que le code TypeScript utilise (pas plus, pas moins). On n'implémente que les fonctions/méthodes réellement appelées dans le projet.

## Code source upstream : `upstream/`

Le dossier `upstream/` contient un clone du repo apk-mitm au commit de référence. Il est ignoré par git (`.gitignore`).

- **`UPSTREAM_COMMIT`** : hash du commit sur lequel le port est basé.
- **`scripts/fetch_upstream.sh`** : clone le repo source au bon commit dans `upstream/`. À lancer avant de commencer le port.

Cela permet de :
- Lire les fichiers TypeScript source localement (`upstream/src/...`) au lieu de fetcher via le réseau.
- Calculer un diff pour rattraper les changements upstream futurs.

Quand on met à jour le port, on met à jour `UPSTREAM_COMMIT` puis on relance le script.

## Methode de travail

Le port se fait en 3 phases séquentielles. Au sein de chaque phase, les sous-agents tournent en parallèle.

### Phase 1 — Scan des imports (1 agent)

Un seul agent scanne tous les fichiers TypeScript du repo source et produit un catalogue des imports externes utilisés, par dépendance. Exemple de sortie :

```
chalk: red, green, yellow, bold, dim
fs: readFile, writeFile, existsSync, mkdir
execa: execa (default export)
...
```

### Phase 2 — Dépendances (N agents en parallèle)

Un agent par fichier de dépendance. Chaque agent reçoit la portion du catalogue qui le concerne et crée le fichier correspondant dans `src/dependencies/`. Les fichiers de dépendances sont indépendants les uns des autres, donc zéro conflit.

### Phase 3 — Code applicatif (agents en parallèle par couche)

On porte les fichiers par couches, du bas vers le haut. Au sein de chaque couche, les agents tournent en parallèle.

1. `src/utils/` + `src/tasks/smali/types.py` (feuilles, pas de deps internes)
2. `src/tasks/smali/` (sauf types.py) + `src/tools/` (dépendent de utils)
3. `src/tasks/` (dépendent de utils, tools, smali)
4. `src/patch_apk.py` + `src/patch_app_bundle.py` (dépendent de tasks/tools)
5. `src/cli.py` + `src/index.py` (dépendent de tout)

### Instructions pour chaque sous-agent

1. Lire le fichier TypeScript source localement depuis `upstream/src/...`.
2. Traduire ligne à ligne en Python en respectant les règles strictes ci-dessus.
3. Écrire le fichier Python résultant dans la structure cible.

## Convention Python

- Pas de `if __name__ == "__main__"` sauf si le fichier TypeScript original a un point d'entrée équivalent.
- Utiliser des `__init__.py` vides dans chaque dossier.
- snake_case pour les noms de fichiers, fonctions, variables.
- PascalCase pour les classes (comme en TypeScript).
- Les interfaces TypeScript deviennent des dataclasses ou TypedDict selon le contexte.
- Les enums TypeScript deviennent des Enum Python.
- Les types union TypeScript deviennent des Union[] avec typing.
- async/await TypeScript → async/await Python avec asyncio.
