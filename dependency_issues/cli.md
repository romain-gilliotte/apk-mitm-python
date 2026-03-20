# Dependency issues for cli.py

## chalk: template interpolation vs tagged template literals

In TypeScript, `chalk` tagged template literals (`` chalk`{yellow ${line}}` ``) treat
interpolated values (`${line}`) as raw text that is NOT parsed for chalk template tokens.
This means if `line` contains `{bold something}`, it would be rendered literally.

In Python, `chalk(f'{{yellow {m.group(0)}}}')` interpolates the matched text into the
template string before passing it to `chalk()`, so any `{` or `}` characters in the
matched text would be processed as chalk template tokens.

This affects `format_command_error()` where regex replacement callbacks use chalk templates
with interpolated match results. If command output contains curly braces, the behavior
will differ from the TypeScript version.

**Fix needed in `src/dependencies/chalk.py`**: Add a way to apply styles to raw text
without parsing it for template tokens (e.g., a method like `chalk.yellow(raw_text)`
that applies styles without template parsing on the argument). The chained method style
(`chalk.yellow(text)`) should already work for this since `_ChalkChain.__call__` applies
styles directly without template parsing.

**Workaround**: Replace `chalk(f'{{yellow {m.group(0)}}}')` with `chalk.yellow(m.group(0))`
in `format_command_error`. Similar changes for `chalk.dim(...)` calls in that function.
This cannot be done in cli.py without deviating from line-by-line port, so it should be
addressed at the dependency level.

## platform.machine() vs process.arch for ARM detection

TypeScript `process.arch.startsWith('arm')` returns `true` for both `'arm'` and `'arm64'`.
Python `platform.machine().startswith('arm')` returns `true` for `'armv7l'` etc., but
`false` for `'aarch64'` (which is what 64-bit ARM reports on Linux).

To match the TypeScript behavior, the check should also include `'aarch64'`:
```python
if platform.machine().startswith('arm') or platform.machine() == 'aarch64':
```

This was kept as-is to avoid deviating from the line-by-line port, but it means the ARM
warning won't show on 64-bit ARM Linux systems.
