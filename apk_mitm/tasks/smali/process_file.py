import platform
import re
from typing import Callable

from apk_mitm.utils import fs
from apk_mitm.dependencies.chalk import chalk
from apk_mitm.dependencies.escape_string_regexp import escape_string_regexp

from apk_mitm.tasks.smali.parse_head import parse_smali_head, SmaliHead
from apk_mitm.tasks.smali.patches import smali_patches
from apk_mitm.tasks.smali.types import SmaliPatch


async def process_smali_file(
    file_path: str,
    log: Callable[[str], None],
) -> bool:
    original_content = await fs.read_file(file_path, 'utf-8')

    if platform.system() == 'Windows':
        # Replace CRLF with LF, so that patches can just use '\n'
        original_content = original_content.replace('\r\n', '\n')

    patched_content = original_content

    smali_head = parse_smali_head(patched_content)
    if smali_head.is_interface:
        return False

    applicable_patches = [
        patch for patch in smali_patches
        if selector_matches_class(patch, smali_head)
    ]
    if len(applicable_patches) == 0:
        return False

    applicable_methods = [
        method
        for patch in applicable_patches
        for method in patch.methods
    ]
    for method in applicable_methods:
        pattern = create_method_pattern(method.signature)

        def make_replacer(method_ref):
            def replacer(match):
                opening_line = match.group(1)
                body = match.group(2)
                closing_line = match.group(3)

                body_lines = [
                    re.sub(r'^    ', '', line)
                    for line in body.split('\n')
                ]

                patched_body_lines = [
                    '# inserted by apk-mitm to disable certificate pinning',
                    *method_ref.replacement_lines,
                    '',
                    '# commented out by apk-mitm to disable old method body',
                    '# ',
                    *[f'# {line}' for line in body_lines],
                ]

                log(
                    chalk(f'{{bold {smali_head.name}}}{{dim :}} Applied {{bold {method_ref.name}}} patch')
                )

                return '\n'.join(
                    line.rstrip()
                    for line in [
                        opening_line,
                        *[f'    {line}' for line in patched_body_lines],
                        closing_line,
                    ]
                )
            return replacer

        patched_content = pattern.sub(make_replacer(method), patched_content)

    if original_content != patched_content:
        if platform.system() == 'Windows':
            # Replace LF with CRLF again
            patched_content = patched_content.replace('\n', '\r\n')

        await fs.write_file(file_path, patched_content)
        return True

    return False


def create_method_pattern(signature: str) -> re.Pattern:
    escaped_signature = escape_string_regexp(signature)
    return re.compile(
        rf'(\.method public (?:final )?{escaped_signature})\n(.+?)\n(\.end method)',
        re.DOTALL,
    )


def selector_matches_class(
    patch: SmaliPatch,
    smali_head: SmaliHead,
) -> bool:
    return (
        # The class matches
        (patch.selector.type == 'class' and
            patch.selector.name == smali_head.name) or
        # One of the implemented interfaces matches
        (patch.selector.type == 'interface' and
            patch.selector.name in smali_head.implements)
    )
