import sys
from functools import cache

import tumfl

from ._utils import INCLUDE_PATHS, normalize_path


@cache
def verify_script(script: str, minify: bool = True) -> str:
    """
    Verify the given script for correctness.
    This is a placeholder function and should be implemented with actual verification logic.
    """
    try:
        parsed = tumfl.parse(script)
    except tumfl.error.TumflError as e:
        if isinstance(e, tumfl.error.ParserError):
            print(e.full_error)
        else:
            print(e)
        sys.exit(1)
    if minify:
        tumfl.minify(parsed)
        return tumfl.format(parsed, style=tumfl.formatter.MinifiedStyle)
    return script


@cache
def resolve_and_verify_script(script_path: str) -> str:
    """
    Resolve dependencies in the given script and verify its correctness.
    """
    try:
        ast = tumfl.resolve_recursive(normalize_path(script_path), INCLUDE_PATHS)
    except tumfl.error.TumflError as e:
        if isinstance(e, tumfl.error.ParserError):
            print(e.full_error)
        else:
            print(e)
        sys.exit(1)
    return tumfl.format(ast)
