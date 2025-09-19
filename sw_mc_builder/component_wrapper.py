from __future__ import annotations

from typing import TYPE_CHECKING

from sw_mc_lib.Component import Component
from sw_mc_lib.Components import CompositeWriteBoolean, CompositeWriteNumber

if TYPE_CHECKING:
    from sw_mc_builder.wire import Wire


class ComponentWrapper:

    def __init__(
        self,
        inner_component: Component,
        inputs: dict[str, Wire],
        component_id: int = -1,
    ):
        self.inner_component: Component = inner_component
        self.inputs: dict[str, Wire] = inputs
        self.component_id: int = component_id
        self.optimize: bool = True
        self.force_property: bool = False

    def to_component(self) -> Component:
        self.inner_component.component_id = self.component_id
        for name, wire in self.inputs.items():
            if wire.component_id is not None:
                input_ = wire.to_input()
                assert input_ is not None
                if name.startswith("channel"):
                    assert isinstance(
                        self.inner_component,
                        (CompositeWriteNumber, CompositeWriteBoolean),
                    )
                    self.inner_component.channel_inputs[int(name.split("_")[1])] = (
                        input_
                    )
                else:
                    setattr(self.inner_component, name, input_)
        return self.inner_component

    def __hash__(self) -> int:
        return hash(id(self))
