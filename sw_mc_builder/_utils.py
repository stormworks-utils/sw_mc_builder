import sys
from pathlib import Path

import tumfl
from sw_mc_lib import Position
from sw_mc_lib.Components import (
    PropertyDropdown,
    PropertyNumber,
    PropertySlider,
    PropertyText,
    PropertyToggle,
)

MAIN_PATH: Path = Path(sys.argv[0]).parent.resolve()

# use newline as statement separator, since it is more readable and does not consume more space
tumfl.formatter.MinifiedStyle.STATEMENT_SEPARATOR = "\n"

PROPERTIES = (
    PropertyNumber,
    PropertySlider,
    PropertyText,
    PropertyToggle,
    PropertyDropdown,
)
PROPERTY_IDS: set[str] = {str(cls(0, Position()).type.value) for cls in PROPERTIES}

BUILDER_IDENTIFIER: str = "Built with sw_mc_builder version 1"

INCLUDE_PATHS: list[Path] = [MAIN_PATH]


def normalize_path(path: str | Path) -> Path:
    """
    Normalize a path by resolving it and converting it to an absolute path.
    """
    if (MAIN_PATH / path).exists():
        return (MAIN_PATH / path).resolve()
    for include_path in INCLUDE_PATHS:
        combined_path = (include_path / path).resolve()
        if combined_path.exists():
            return combined_path
    raise FileNotFoundError(f"Could not find path: {path}")


def add_include_path(path: str | Path) -> None:
    """
    Add a path to the list of include paths for resolving scripts and script dependencies.
    """
    normalized_path = normalize_path(path)
    if normalized_path not in INCLUDE_PATHS:
        INCLUDE_PATHS.append(normalized_path)
