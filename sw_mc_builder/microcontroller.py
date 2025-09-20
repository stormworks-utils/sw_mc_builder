import warnings
from pathlib import Path
from typing import Optional

from sw_mc_lib import Node, NodePosition, Position, XMLParserElement
from sw_mc_lib.Components import (
    PropertyDropdown,
    PropertyNumber,
    PropertySlider,
    PropertyText,
    PropertyToggle,
    TooltipBoolean,
    TooltipNumber,
)
from sw_mc_lib.layout import layout_mc
from sw_mc_lib.Microcontroller import MCImage
from sw_mc_lib.Microcontroller import Microcontroller as SWMicrocontroller
from sw_mc_lib.optimizer import (
    optimize_composite_writes,
    optimize_functions,
    optimize_tree,
)
from sw_mc_lib.Types import NodeMode, SignalType, TooltipMode

from sw_mc_builder.component_wrapper import ComponentWrapper
from sw_mc_builder.pseudo_components import InputPlaceholder, PseudoComponent
from sw_mc_builder.wire import BooleanInput, NumberInput, Wire

from ._utils import BUILDER_IDENTIFIER, PROPERTIES
from .optimizer import optimize_arithmetic


class Microcontroller:
    def __init__(
        self,
        name: str,
        width: int = 2,
        length: int = 2,
        description: str = "No description set.",
        save_name: Optional[str] = None,
    ):
        self._mc: SWMicrocontroller = SWMicrocontroller(
            name, description, width, length, [], []
        )
        self._save_name: str = save_name or name
        self._placed_inputs: set[InputPlaceholder] = set()
        self.optimize: bool = True
        self._placed_outputs: list[tuple[Wire, Node]] = []
        self._additional_components: list[ComponentWrapper] = []
        self._warned_placement: bool = False
        self._properties: set[ComponentWrapper] = set()

    def stop_optimization(self) -> None:
        self.optimize = False

    def add_image_from_file(self, file_path: Path) -> None:
        self._mc.image = MCImage.from_png(file_path)

    def add_image_from_list(self, pixels: list[list[bool]]) -> None:
        self._mc.image = MCImage(pixels)

    def save_image(self, path: Path) -> None:
        self._mc.image.to_png(path)

    def _validate_placement(self, position: NodePosition) -> None:
        for node in self._mc.nodes:
            if node.position == position:
                raise ValueError(f"Node already exists at position {position}")
        if position.x >= 6 or position.z >= 6 or position.x < 0 or position.z < 0:
            raise ValueError(f"Node position out of bounds {position}")
        if position.x >= self._mc.width or position.z >= self._mc.length:
            if not self._warned_placement:
                warnings.warn(
                    f"Warning: Placing node at {position} which is outside the microcontroller bounds ({self._mc.width}, {self._mc.length}). Microcontroller will be expanded.",
                    stacklevel=3,
                )
                self._warned_placement = True
            self._mc.width = max(self._mc.width, position.x + 1)
            self._mc.length = max(self._mc.length, position.z + 1)

    def place_input(self, input_: Wire, x: int = 0, y: int = 0) -> None:
        if not isinstance(input_.producer, InputPlaceholder):
            raise TypeError("Input must be produced by an InputPlaceholder")
        if input_.producer in self._placed_inputs:
            raise ValueError(f"Input {input_.producer.name} already placed")
        position: NodePosition = NodePosition(x, y)
        self._validate_placement(position)
        self._mc.add_new_node(
            Node(
                0,
                0,
                input_.producer.name,
                NodeMode.Input,
                input_.wire_type,
                input_.producer.description,
                NodePosition(x, y),
            )
        )
        input_.producer.component_id = self._mc.nodes[-1].component_id
        self._placed_inputs.add(input_.producer)

    def place_output(
        self,
        input_: Wire,
        name: str,
        description: str = "The processed output signal.",
        x: int = 0,
        y: int = 0,
    ) -> None:
        position: NodePosition = NodePosition(x, y)
        self._validate_placement(position)
        self._mc.add_new_node(
            Node(
                0,
                0,
                name,
                NodeMode.Output,
                input_.wire_type,
                description,
                NodePosition(x, y),
                input=input_.to_input(),
            )
        )
        self._placed_outputs.append((input_, self._mc.nodes[-1]))

    def add_number_tooltip(
        self,
        name: str = "value",
        display_number: NumberInput = None,
        is_error: BooleanInput = None,
        display: TooltipMode = TooltipMode.Always,
    ) -> None:
        self._additional_components.append(
            ComponentWrapper(
                TooltipNumber(-1, Position(0, 0), name, display),
                {
                    "display_number_input": Wire.to(SignalType.Number, display_number),
                    "is_error_input": Wire.to(SignalType.Boolean, is_error),
                },
            )
        )

    def add_boolean_tooltip(
        self,
        name: str = "value",
        value: BooleanInput = None,
        on_label: str = "on",
        off_label: str = "off",
        display: TooltipMode = TooltipMode.Always,
    ) -> None:
        self._additional_components.append(
            ComponentWrapper(
                TooltipBoolean(-1, Position(0, 0), name, on_label, off_label, display),
                {
                    "display_number_input": Wire.to(SignalType.Boolean, value),
                },
            )
        )

    def add_property(self, property: Wire) -> None:
        if not isinstance(property.producer, ComponentWrapper):
            raise TypeError("Property must be produced by a ComponentWrapper")
        if not isinstance(
            property.producer.inner_component,
            (PropertyNumber, PropertySlider, PropertyToggle, PropertyDropdown),
        ):
            raise TypeError("Property must be a valid property component")
        self._additional_components.append(property.producer)

    def add_text_property(
        self, name: str, content: str, force_property: bool = False
    ) -> None:
        component = ComponentWrapper(
            PropertyText(-1, Position(0, 0), name, content),
            {},
        )
        component.force_property = force_property
        self._additional_components.append(component)

    def _resolve(self) -> None:
        to_visit: set[ComponentWrapper | PseudoComponent] = set()
        visited_nodes: set[ComponentWrapper | PseudoComponent] = set()
        visited_components: set[ComponentWrapper] = set()
        next_id: int = self._mc.id_counter + 1
        for node_source, _ in self._placed_outputs:
            to_visit.add(node_source.producer)

        for component in self._additional_components:
            # This is done separately in order for the order to be represented in the final microcontroller
            # This is especially relevant for tooltips (as they are shown in order)
            for input_wire in component.inputs.values():
                to_visit.add(input_wire.producer)
            visited_components.add(component)
            if isinstance(component.inner_component, PROPERTIES):
                self._properties.add(component)
            component.component_id = next_id
            next_id += 1

        while to_visit:
            current = to_visit.pop()
            if current in visited_nodes:
                continue
            visited_nodes.add(current)

            if isinstance(current, ComponentWrapper):
                for input_wire in current.inputs.values():
                    to_visit.add(input_wire.producer)
                visited_components.add(current)
                if isinstance(current.inner_component, PROPERTIES):
                    self._properties.add(current)
                current.component_id = next_id
                next_id += 1
            elif isinstance(current, InputPlaceholder):
                if current not in self._placed_inputs:
                    raise ValueError(
                        f"Input {current.name} not placed in microcontroller"
                    )

        for wire, node in self._placed_outputs:
            node.input = wire.to_input()
            if node.input:
                node.input.index = "1"

        for component in visited_components:
            self._mc.components.append(component.to_component())

    def _resolve_and_optimize(self) -> XMLParserElement:
        if self.optimize:
            wires = [
                wire
                for component in self._additional_components
                for wire in component.inputs.values()
            ]
            for node, _ in self._placed_outputs:
                wires.append(node)
            optimize_arithmetic(wires)
        self._resolve()
        optimize_composite_writes(self._mc)
        optimize_functions(self._mc)
        optimize_tree(self._mc)
        layout_mc(self._mc)
        mc_xml = self._mc.to_xml()

        group = mc_xml.children[1]
        assert group.tag == "group"
        data = group.children[0]
        assert data.tag == "data"
        data.attributes["desc"] = BUILDER_IDENTIFIER

        properties = {
            str(prop.component_id): prop
            for prop in self._properties
            if prop.force_property
        }
        components = group.children[1]
        assert components.tag == "components"
        for component in components.children:
            obj = component.children[0]
            assert obj.tag == "object"
            if obj.attributes.get("id", "0") in properties:
                obj.attributes["force_property"] = "1"

        return mc_xml
