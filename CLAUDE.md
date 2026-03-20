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
src/cli.ts                   →  apk_mitm/cli.py
src/index.ts                 →  apk_mitm/index.py
src/patch_apk.ts             →  apk_mitm/patch_apk.py
src/patch_app_bundle.ts      →  apk_mitm/patch_app_bundle.py
src/tasks/apply_patches.ts   →  apk_mitm/tasks/apply_patches.py
src/tasks/check_prerequisites.ts → apk_mitm/tasks/check_prerequisites.py
src/tasks/copy_certificate_file.ts → apk_mitm/tasks/copy_certificate_file.py
src/tasks/create_netsec_config.ts → apk_mitm/tasks/create_netsec_config.py
src/tasks/disable_certificate_pinning.ts → apk_mitm/tasks/disable_certificate_pinning.py
src/tasks/download_tools.ts  →  apk_mitm/tasks/download_tools.py
src/tasks/modify_manifest.ts →  apk_mitm/tasks/modify_manifest.py
src/tasks/smali/parse_head.ts → apk_mitm/tasks/smali/parse_head.py
src/tasks/smali/patches.ts   →  apk_mitm/tasks/smali/patches.py
src/tasks/smali/process_file.ts → apk_mitm/tasks/smali/process_file.py
src/tasks/smali/types.ts     →  apk_mitm/tasks/smali/types.py
src/tools/apktool.ts         →  apk_mitm/tools/apktool.py
src/tools/tool.ts            →  apk_mitm/tools/tool.py
src/tools/uber_apk_signer.ts →  apk_mitm/tools/uber_apk_signer.py
src/utils/build_glob.ts      →  apk_mitm/utils/build_glob.py
src/utils/download_file.ts   →  apk_mitm/utils/download_file.py
src/utils/download_tool.ts   →  apk_mitm/utils/download_tool.py
src/utils/execute_jar.ts     →  apk_mitm/utils/execute_jar.py
src/utils/fs.ts              →  apk_mitm/utils/fs.py
src/utils/get_java_version.ts → apk_mitm/utils/get_java_version.py
src/utils/observe_async.ts   →  apk_mitm/utils/observe_async.py
src/utils/observe_listr.ts   →  apk_mitm/utils/observe_listr.py
src/utils/observe_process.ts →  apk_mitm/utils/observe_process.py
src/utils/user_error.ts      →  apk_mitm/utils/user_error.py
```

Les noms de fichiers passent de camelCase/kebab-case à snake_case (convention Python).

## Couche de dépendances : `apk_mitm/dependencies/`

Les dépendances TypeScript sont encapsulées dans `apk_mitm/dependencies/`, un fichier par dépendance. Chaque fichier expose **la même interface** que le module TypeScript original (mêmes noms de fonctions/classes, mêmes signatures). L'implémentation interne utilise des libs Python, mais le code appelant n'a pas besoin de le savoir.

Cela permet au code porté de rester le plus proche possible de l'original : au lieu de réécrire les appels, on importe depuis `apk_mitm.dependencies.<module>`.

```
apk_mitm/dependencies/
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
from apk_mitm.dependencies.chalk import chalk
```

L'interface exposée par chaque fichier dans `apk_mitm/dependencies/` doit correspondre exactement à ce que le code TypeScript utilise (pas plus, pas moins). On n'implémente que les fonctions/méthodes réellement appelées dans le projet.

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

Un agent par fichier de dépendance. Chaque agent reçoit la portion du catalogue qui le concerne et crée le fichier correspondant dans `apk_mitm/dependencies/`. Les fichiers de dépendances sont indépendants les uns des autres, donc zéro conflit.

Pour implémenter chaque dépendance, le sous-agent peut généralement se baser sur les appels dans le code source TypeScript (`upstream/src/`) pour déduire l'API à reproduire. En cas de doute sur le comportement exact d'une lib, les `node_modules` du repo upstream sont disponibles (`upstream/node_modules/`) — les deps npm sont installées — et peuvent être consultés pour comprendre la signature, les options, ou le comportement d'une fonction.

### Phase 3 — Code applicatif (agents en parallèle par couche)

On porte les fichiers par couches, du bas vers le haut. Au sein de chaque couche, les agents tournent en parallèle.

1. `apk_mitm/utils/` + `apk_mitm/tasks/smali/types.py` (feuilles, pas de deps internes)
2. `apk_mitm/tasks/smali/` (sauf types.py) + `apk_mitm/tools/` (dépendent de utils)
3. `apk_mitm/tasks/` (dépendent de utils, tools, smali)
4. `apk_mitm/patch_apk.py` + `apk_mitm/patch_app_bundle.py` (dépendent de tasks/tools)
5. `apk_mitm/cli.py` + `apk_mitm/index.py` (dépendent de tout)

### Instructions pour chaque sous-agent

1. Lire le fichier TypeScript source localement depuis `upstream/src/...`.
2. Traduire ligne à ligne en Python en respectant les règles strictes ci-dessus.
3. Écrire le fichier Python résultant dans la structure cible.

### Règle Phase 3 : ne pas modifier les dépendances

Pendant la phase 3, les sous-agents **ne doivent jamais modifier** les fichiers dans `apk_mitm/dependencies/`. Si un sous-agent rencontre un problème avec une dépendance (fonction manquante, signature incorrecte, comportement inattendu), il doit :

1. Écrire le code applicatif en supposant que la dépendance sera corrigée plus tard (utiliser l'API attendue).
2. Créer un fichier `dependency_issues/<nom_du_fichier_porté>.md` décrivant le problème : quelle dépendance, quelle fonction/méthode manquante ou incorrecte, et ce qui est attendu.

Cela évite les éditions concurrentes sur les fichiers de dépendances quand plusieurs agents tournent en parallèle. Une passe de correction des dépendances sera faite après la phase 3.

## Règle absolue : ne pas modifier le code sans demande explicite

Ne jamais modifier un fichier source Python déjà porté sauf si l'utilisateur le demande explicitement. Quand un problème est détecté (import circulaire, bug, etc.), le signaler à l'utilisateur et attendre ses instructions avant de toucher au code.

### Exception : imports circulaires

En TypeScript, les imports de types sont effacés au runtime, donc pas de circulaire. Pour reproduire ce comportement en Python, il est OK d'utiliser `from __future__ import annotations` + `if TYPE_CHECKING:` pour les imports qui ne concernent que des types (ex: `TaskOptions`). Ceci est considéré comme faisant partie du port fidèle, pas comme une modification.

## Tooling

- **uv** est utilisé comme gestionnaire de projet/dépendances. Utiliser `uv run` pour exécuter du code Python (ex: `uv run python -c "..."`, `uv run python -m apk_mitm.cli`).

## Convention Python

- Pas de `if __name__ == "__main__"` sauf si le fichier TypeScript original a un point d'entrée équivalent.
- Utiliser des `__init__.py` vides dans chaque dossier.
- snake_case pour les noms de fichiers, fonctions, variables.
- PascalCase pour les classes (comme en TypeScript).
- Les enums TypeScript deviennent des Enum Python.
- Les types union TypeScript deviennent des Union[] avec typing.
- async/await TypeScript → async/await Python avec asyncio.

### Objets JS → Python : dict vs dataclass

En JavaScript, `{ foo: 1, bar: 2 }` est à la fois un objet littéral et une structure de données. En Python, on choisit selon l'usage dans le code TypeScript source :

- **`@dataclass`** : quand le TS définit une `interface` ou un `type` nommé qui sert de structure avec des champs connus, et que le code accède aux champs par `.propriété` (ex: `SmaliPatch`, `ToolVersion`, `SmaliHead`).
- **`dict`** : quand le TS passe un objet littéral anonyme (ex: options `{ zipalign: true }`, retour `{ usesAppBundle: true }`, context Listr). Le code Python accède alors par `result["key"]`, pas `result.key`.

**Règle simple** : si le TS a un `interface`/`type` nommé → `@dataclass`. Si c'est un objet littéral inline → `dict`.

**Piège courant** : quand une fonction retourne un dict, le code appelant doit utiliser `result["key"]` et non `result.key`. Attention aux `.` dans le code porté qui devraient être des `[""]`.
