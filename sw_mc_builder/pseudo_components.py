# pylint: disable=too-few-public-methods
from __future__ import annotations


class PseudoComponent:
    """A pseudo component acing as a marker for the builder. Not a subclass of Component"""


class Unconnected(PseudoComponent):
    """A constant component that outputs nothing and has no size. Not a subclass of Placeholder"""


class Placeholder(PseudoComponent):
    """A placeholder component that does nothing and has no size."""


class InputPlaceholder(PseudoComponent):
    """A placeholder component that represents an input to the microcontroller."""

    def __init__(self, component_id: int, name: str, description: str) -> None:
        self.name: str = name
        self.component_id: int = component_id
        self.description: str = description
