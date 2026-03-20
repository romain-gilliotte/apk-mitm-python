import re
from dataclasses import dataclass
from typing import List


CLASS_PATTERN = re.compile(r'\.class(?P<keywords>.+)? L(?P<name>[^\s]+);')
IMPLEMENTS_PATTERN = re.compile(r'\.implements L(?P<name>[^\s]+);')


@dataclass
class SmaliHead:
    # The name of the class.
    name: str

    # The interfaces implemented by this class.
    implements: List[str]

    # Whether the "class" actually represents an interface.
    is_interface: bool


def parse_smali_head(contents: str) -> SmaliHead:
    match = CLASS_PATTERN.search(contents)
    keywords = match.group('keywords')
    name = match.group('name')

    return SmaliHead(
        name=name,
        implements=[
            m.group('name') for m in IMPLEMENTS_PATTERN.finditer(contents)
        ],
        is_interface='interface' in keywords.strip().split(' ') if keywords else False,
    )
