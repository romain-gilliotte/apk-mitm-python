# Dependency issues for `src/patch_apk.py`

## `src/dependencies/rxjs.py` — Missing `for_each` method on `Observable`

Same issue as documented in `dependency_issues/download_tool.md`.

The TypeScript code uses `Observable.forEach()` in two places:

```typescript
await apktool.encode(decodeDir, tmpApkPath, true).forEach(next)
```

```typescript
await uberApkSigner.sign([tmpApkPath], { zipalign: true }).forEach(line => log(line))
```

The Python `Observable` class in `src/dependencies/rxjs.py` does not have a `for_each` method.

## `src/tools/uber_apk_signer.py` — `sign()` signature mismatch

The TypeScript code calls `uberApkSigner.sign([tmpApkPath], { zipalign: true })` passing an options object as the second argument. The Python `UberApkSigner.sign()` takes `zipalign` as a direct keyword argument (`def sign(self, input_paths, zipalign=False)`), not as a dict.

The ported code passes `{"zipalign": True}` as the second argument to match the TypeScript pattern (and to match `patch_app_bundle.py` which does the same). The `sign()` method signature should be updated to accept a dict, or the callers should be updated to use keyword arguments.
