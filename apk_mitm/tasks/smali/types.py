from dataclasses import dataclass
from typing import List, Literal


@dataclass
class SmaliPatchSelector:
    # The criterion used to match a class.
    type: Literal['interface', 'class']

    # The exact name of the class or interface including the package.
    name: str


@dataclass
class SmaliMethodPatch:
    # A descriptive name of the patch including the name of the class, the name
    # of the method, and the library the class belongs to.
    name: str

    # The Smali signature of the method including the name, the parameter types,
    # and the return type, but _excluding_ modifiers (like `public` or `final`).
    signature: str

    # An array of the Smali lines that are used to replace the method body
    # _without_ leading indentation (that's prepended automatically).
    replacement_lines: List[str]


@dataclass
class SmaliPatch:
    # A selector that identifies the classes that this patch can be applied to
    # based on either an exact class name or an interface the class implements.
    selector: SmaliPatchSelector

    # The patches that can be applied to the methods of the class.
    methods: List[SmaliMethodPatch]
