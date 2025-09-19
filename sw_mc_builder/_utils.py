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
