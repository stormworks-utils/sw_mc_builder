from __future__ import annotations

import re
from typing import Optional

from sw_mc_lib.Components import (
    AND,
    NAND,
    NOR,
    NOT,
    OR,
    XOR,
    Abs,
    Add,
    ArithmeticFunction8In,
    BooleanFunction8In,
    Clamp,
    CompositeWriteBoolean,
    CompositeWriteNumber,
    ConstantNumber,
    ConstantOn,
    Divide,
    Equal,
    GreaterThan,
    LessThan,
    Modulo,
    Multiply,
    NumericalSwitchbox,
    Subtract,
    Threshold,
    UpDownCounter,
)
from sw_mc_lib.Types import SignalType

import sw_mc_builder.components as comp
from sw_mc_builder import wire

from .component_wrapper import ComponentWrapper
from .pseudo_components import PseudoComponent, Unconnected


def wire_to_id(w: wire.Wire) -> str:
    # deterministic one way function to get a unique id for a wire
    return str(id(w))


def process_and(inputs: dict[str, wire.Wire]) -> Optional[tuple[str, set[wire.Wire]]]:
    input_a = inner_optimize_numerical_boolean(inputs["a_input"])
    input_b = inner_optimize_numerical_boolean(inputs["b_input"])
    if input_a is None or input_b is None:
        return None
    true_a, used_wires_a = input_a
    true_b, used_wires_b = input_b
    true_func = f"({true_a}*{true_b})"
    return true_func, used_wires_a.union(used_wires_b)


def process_or(inputs: dict[str, wire.Wire]) -> Optional[tuple[str, set[wire.Wire]]]:
    input_a = inner_optimize_numerical_boolean(inputs["a_input"])
    input_b = inner_optimize_numerical_boolean(inputs["b_input"])
    if input_a is None or input_b is None:
        return None
    true_a, used_wires_a = input_a
    true_b, used_wires_b = input_b
    true_func = f"max({true_a},{true_b})"
    return true_func, used_wires_a.union(used_wires_b)


def process_xor(inputs: dict[str, wire.Wire]) -> Optional[tuple[str, set[wire.Wire]]]:
    input_a = inner_optimize_numerical_boolean(inputs["a_input"])
    input_b = inner_optimize_numerical_boolean(inputs["b_input"])
    if input_a is None or input_b is None:
        return None
    true_a, used_wires_a = input_a
    true_b, used_wires_b = input_b
    true_func = f"abs({true_a}-{true_b})"
    return true_func, used_wires_a.union(used_wires_b)


def process_not(inputs: dict[str, wire.Wire]) -> Optional[tuple[str, set[wire.Wire]]]:
    input_ = inner_optimize_numerical_boolean(inputs["a_input"])
    if input_ is None:
        return None
    true_func, used_wires = input_
    return f"(1-{true_func})", used_wires


def get_input(
    inputs: dict[str, wire.Wire], name: str, result_wires: set[wire.Wire]
) -> str:
    input_value = inputs[name]
    if isinstance(input_value.producer, ComponentWrapper):
        if isinstance(input_value.producer.inner_component, ConstantNumber):
            return input_value.producer.inner_component.value_property.text
    if isinstance(input_value.producer, Unconnected):
        return "0"
    result_wires.add(input_value)
    return wire_to_id(input_value)


def inner_optimize_numerical_boolean(
    input_wire: wire.Wire,
    first_iteration: bool = False,
) -> Optional[tuple[str, set[wire.Wire]]]:
    # pylint: disable=too-many-locals
    if isinstance(input_wire.producer, Unconnected):
        return "0", set()
    if not isinstance(input_wire.producer, ComponentWrapper):
        if first_iteration:
            return None
        switch_res = comp.numerical_switchbox(1, 0, input_wire)
        return wire_to_id(switch_res), {switch_res}
    component: ComponentWrapper = input_wire.producer
    if not component.optimize:
        return None
    inner = component.inner_component
    inputs = component.inputs
    result_wires: set[wire.Wire] = set()
    if isinstance(inner, Equal):
        epsilon = inner.epsilon_property.value
        a = get_input(inputs, "a_input", result_wires)
        b = get_input(inputs, "b_input", result_wires)
        true_func: str = f"((1-sgn(abs({a}-{b})-{epsilon}))/2)"
        if epsilon == 0:
            true_func = f"((sgn({a}-{b})+sgn({b}-{a}))/2)"
        return true_func, result_wires
    if isinstance(inner, GreaterThan):
        a = get_input(inputs, "a_input", result_wires)
        b = get_input(inputs, "b_input", result_wires)
        true_func = f"((1-sgn({b}-{a}))/2)"
        return true_func, result_wires
    if isinstance(inner, LessThan):
        a = get_input(inputs, "a_input", result_wires)
        b = get_input(inputs, "b_input", result_wires)
        true_func = f"((1-sgn({a}-{b}))/2)"
        return true_func, result_wires
    if isinstance(inner, Threshold):
        max_ = inner.max_property.value
        min_ = inner.min_property.value
        a = get_input(inputs, "a_input", result_wires)
        true_func = f"(((sgn({a}-{min_})+1)/2)*((sgn({max_}-{a})+1)/2))"
        return true_func, result_wires
    if isinstance(inner, NOT):
        input_ = inner_optimize_numerical_boolean(component.inputs["a_input"])
        if input_ is None:
            return None
        true_func, used_wires = input_
        return f"(1-{true_func})", used_wires
    if isinstance(inner, AND):
        return process_and(component.inputs)
    if isinstance(inner, NAND):
        and_result = process_and(component.inputs)
        if and_result is None:
            return None
        return f"(1-{and_result[0]})", and_result[1]
    if isinstance(inner, OR):
        return process_or(component.inputs)
    if isinstance(inner, NOR):
        or_result = process_or(component.inputs)
        if or_result is None:
            return None
        return f"(1-{or_result[0]})", or_result[1]
    if isinstance(inner, XOR):
        return process_xor(component.inputs)
    if isinstance(inner, ConstantOn):
        return "1", set()
    if first_iteration:
        return None
    switch_res = comp.numerical_switchbox(1, 0, input_wire)
    return wire_to_id(switch_res), {switch_res}


def optimize_numerical_boolean(
    input_wire: wire.Wire,
    extra_count: int = 0,
) -> Optional[tuple[str, dict[str, wire.Wire], list[str]]]:
    optimization_result = inner_optimize_numerical_boolean(
        input_wire, first_iteration=True
    )
    if optimization_result is None:
        return None
    true_func, used_wires = optimization_result
    if len(used_wires) + extra_count > 8:
        return None
    available_names = ["x", "y", "z", "w", "a", "b", "c", "d"]
    wire_associations: dict[str, wire.Wire] = {}
    for wire_ in used_wires:
        name = available_names.pop(0)
        true_func = true_func.replace(wire_to_id(wire_), name)
        wire_associations[name] = wire_
    return (
        true_func,
        wire_associations,
        [available_names.pop(0) for _ in range(extra_count)],
    )


def optimize_component(
    component: ComponentWrapper,
) -> Optional[ComponentWrapper | PseudoComponent]:
    inner = component.inner_component
    inputs = component.inputs
    if isinstance(inner, ArithmeticFunction8In):
        return comp.function(
            inner.function, **{k.replace("_input", ""): v for k, v in inputs.items()}
        ).producer
    if isinstance(inner, Add):
        return comp.function("x+y", inputs["a_input"], inputs["b_input"]).producer
    if isinstance(inner, Subtract):
        return comp.function("x-y", inputs["a_input"], inputs["b_input"]).producer
    if isinstance(inner, Multiply):
        return comp.function("x*y", inputs["a_input"], inputs["b_input"]).producer
    if isinstance(inner, Divide):
        return comp.function("x/y", inputs["a_input"], inputs["b_input"]).producer
    if isinstance(inner, Modulo):
        return comp.function("x%y", inputs["a_input"], inputs["b_input"]).producer
    if isinstance(inner, Abs):
        return comp.function("abs(x)", inputs["number_input"]).producer
    if isinstance(inner, Clamp):
        return comp.function(
            f"clamp(x,{inner.min_property.text},{inner.max_property.text})",
            inputs["number_input"],
        ).producer
    if isinstance(inner, ConstantNumber):
        return comp.function(inner.value_property.text).producer
    if isinstance(inner, BooleanFunction8In):
        return comp.boolean_function(
            inner.function, **{k.replace("_input", ""): v for k, v in inputs.items()}
        ).producer
    if isinstance(inner, ConstantOn):
        return comp.boolean_function("true").producer
    if isinstance(inner, AND):
        return comp.boolean_function(
            "x&y", inputs["a_input"], inputs["b_input"]
        ).producer
    if isinstance(inner, NAND):
        return comp.boolean_function(
            "!(x&y)", inputs["a_input"], inputs["b_input"]
        ).producer
    if isinstance(inner, OR):
        return comp.boolean_function(
            "x|y", inputs["a_input"], inputs["b_input"]
        ).producer
    if isinstance(inner, NOR):
        return comp.boolean_function(
            "!(x|y)", inputs["a_input"], inputs["b_input"]
        ).producer
    if isinstance(inner, XOR):
        return comp.boolean_function(
            "x^y", inputs["a_input"], inputs["b_input"]
        ).producer
    if isinstance(inner, NOT):
        return comp.boolean_function("!x", inputs["a_input"]).producer
    return None


def get_input_count(component: ComponentWrapper) -> int:
    return sum(
        0 if isinstance(input_wire.producer, Unconnected) else 1
        for input_wire in component.inputs.values()
    )


class Optimizer:
    def __init__(self, components: list[ComponentWrapper]):
        self.components: list[ComponentWrapper] = components
        self.optimized_components: dict[ComponentWrapper, ComponentWrapper] = {}
        self.to_visit: set[ComponentWrapper] = set(components)
        self.in_progress: set[ComponentWrapper] = set()

    def find_optimizations(self, component: ComponentWrapper) -> ComponentWrapper:
        # pylint: disable=too-many-locals,too-many-boolean-expressions
        if component in self.optimized_components:
            return self.optimized_components[component]

        self.in_progress.add(component)

        if not component.optimize:
            self.optimized_components[component] = component
            self.in_progress.remove(component)
            return component

        input_count = get_input_count(component)

        replacements: dict[str, str] = {}
        input_replacements: dict[str, wire.Wire] = {}
        present_inputs: dict[wire.Wire, str] = {}
        available_names: list[str] = ["x", "y", "z", "w", "a", "b", "c", "d"]
        potential_optimizations: list[tuple[int, str, ComponentWrapper, wire.Wire]] = []

        optimized = optimize_component(component)

        if optimized is None:
            inputs = component.inputs
            if isinstance(component.inner_component, NumericalSwitchbox):
                # try to optimize switch signal
                on_prod = inputs["on_value_input"]
                off_prod = inputs["off_value_input"]
                optimization_result = optimize_numerical_boolean(
                    inputs["switch_signal_input"], 2
                )
                if optimization_result is not None:
                    true_func, wire_associations, [on_name, off_name] = (
                        optimization_result
                    )
                    false_func = f"(1-{true_func})"
                    optimized = comp.function(
                        f"({true_func})*{on_name}+({false_func})*{off_name}",
                        **{on_name: on_prod, off_name: off_prod, **wire_associations},
                    ).producer
            elif isinstance(component.inner_component, UpDownCounter):
                up_optimized = inner_optimize_numerical_boolean(inputs["up_input"])
                down_optimized = inner_optimize_numerical_boolean(inputs["down_input"])
                reset_optimized = inner_optimize_numerical_boolean(
                    inputs["reset_input"]
                )
                min_value = component.inner_component.min_property.value
                max_value = component.inner_component.max_property.value
                increment_value = component.inner_component.increment_property.value
                clamp_value = component.inner_component.clamp
                if (
                    up_optimized is not None
                    and down_optimized is not None
                    and reset_optimized is not None
                ):
                    up_func, up_wires = up_optimized
                    down_func, down_wires = down_optimized
                    reset_func, reset_wires = reset_optimized
                    all_wires = up_wires.union(down_wires).union(reset_wires)
                    if len(all_wires) <= 7:  # need one extra for self reference
                        available_names = ["x", "y", "z", "w", "a", "b", "c", "d"]
                        wire_associations = {}
                        for wire_ in all_wires:
                            name = available_names.pop(0)
                            up_func = up_func.replace(wire_to_id(wire_), name)
                            down_func = down_func.replace(wire_to_id(wire_), name)
                            reset_func = reset_func.replace(wire_to_id(wire_), name)
                            wire_associations[name] = wire_
                        result = comp.placeholder(SignalType.Number)
                        self_name: str = available_names.pop(0)
                        wire_associations[self_name] = result
                        value = f"({self_name}+{increment_value}*{up_func}-{increment_value}*{down_func})"
                        if clamp_value:
                            value = f"clamp({value},{min_value},{max_value})"
                        result.replace_producer(
                            comp.function(
                                f"(1-{reset_func})*{value}+{reset_func}*{min_value}",
                                **wire_associations,
                            )
                        )
                        optimized = result.producer
            elif (
                isinstance(
                    component.inner_component,
                    (CompositeWriteBoolean, CompositeWriteNumber),
                )
                and component.inner_component.start_channel_property == 1
                and (other := component.inputs.get("composite_signal_input"))
                is not None
                and isinstance(other.producer, ComponentWrapper)
                and isinstance(
                    other.producer.inner_component, type(component.inner_component)
                )
                and isinstance(
                    other.producer.inner_component,
                    (CompositeWriteBoolean, CompositeWriteNumber),
                )
                and other.producer.inner_component.start_channel_property == 1
                and other.producer.optimize
            ):
                for i in range(1, 33):
                    name = f"channel_{i}_input"
                    if isinstance(component.inputs[name].producer, Unconnected):
                        component.inputs[name] = other.producer.inputs[name]
                component.inputs["composite_signal_input"] = other.producer.inputs[
                    "composite_signal_input"
                ]

            assert optimized is None or isinstance(optimized, ComponentWrapper)
            self.optimized_components[component] = (
                component if optimized is None else self.find_optimizations(optimized)
            )
            self.in_progress.remove(component)
            return component if optimized is None else optimized

        assert isinstance(optimized, ComponentWrapper)
        assert isinstance(
            optimized.inner_component, (ArithmeticFunction8In, BooleanFunction8In)
        )
        self_references: set[str] = {
            name
            for name, input_wire in optimized.inputs.items()
            if input_wire.producer is component
        }

        for name, input_wire in optimized.inputs.items():
            raw_optimized = None
            if (
                isinstance(input_wire.producer, ComponentWrapper)
                and input_wire.producer not in self.in_progress
            ):
                raw_optimized = self.find_optimizations(input_wire.producer)
            if (
                isinstance(input_wire.producer, ComponentWrapper)
                and input_wire.producer.optimize
                and input_wire.producer not in self.in_progress
                and raw_optimized is not None
                and not any(
                    w.producer is raw_optimized for w in raw_optimized.inputs.values()
                )
            ):
                optimized_input = optimize_component(raw_optimized)
                if optimized_input is not None:
                    assert isinstance(optimized_input, ComponentWrapper)
                    potential_optimizations.append(
                        (
                            get_input_count(optimized_input) - 1,
                            name,
                            optimized_input,
                            input_wire,
                        )
                    )
                    continue
            if not isinstance(input_wire.producer, Unconnected):
                # keep input as is, and remove from available names
                shortened_name = name.replace("_input", "")
                available_names.remove(shortened_name)
                present_inputs[input_wire] = shortened_name
            else:
                # set unconnected inputs to 0, so that future assignments to these names work
                optimized.inner_component.function = re.sub(
                    rf"\b{name.replace('_input', '')}\b",
                    "0" if input_wire.wire_type == SignalType.Number else "false",
                    optimized.inner_component.function,
                )

        potential_optimizations.sort(key=lambda x: x[0])

        while sum(i[0] for i in potential_optimizations) + input_count > 8:
            # remove the optimization that saves the most inputs
            _, name, _, _ = potential_optimizations.pop()
            available_names.remove(name.replace("_input", ""))

        if not potential_optimizations:
            self.optimized_components[component] = component
            self.in_progress.remove(component)
            return component

        for _, name, optimized_input, input_wire in potential_optimizations:
            assert isinstance(
                optimized_input.inner_component,
                (ArithmeticFunction8In, BooleanFunction8In),
            )
            # rename variables in function to placeholder names (w_input_a, w_input_b, ...)
            function: str = optimized_input.inner_component.function
            for inner_name, inner_wire in optimized_input.inputs.items():
                var: str = inner_name.replace("_input", "")
                if not isinstance(inner_wire.producer, Unconnected):
                    if inner_wire in present_inputs:
                        input_count -= 1
                    new_name: str = f"{name}_{var}"
                    # remember new input
                    input_replacements[new_name] = inner_wire
                    function = re.sub(rf"\b{var}\b", new_name, function)
            # remember replacement in parent function
            replacements[name.replace("_input", "")] = f"({function})"
            # mark input as unconnected (can be reassigned later)
            optimized.inputs[name] = wire.Wire(input_wire.wire_type, Unconnected())

        new_function = optimized.inner_component.function
        # apply replacements
        for old, new in replacements.items():
            new_function = re.sub(rf"\b{old}\b", new, new_function)

        for name, new_wire in input_replacements.items():
            if new_wire in present_inputs:  # pylint: disable=consider-using-get
                # input already present, reuse name
                new_name = present_inputs[new_wire]
            else:
                new_name = available_names.pop(0)
            new_function = new_function.replace(name, new_name)
            optimized.inputs[f"{new_name}_input"] = new_wire
            if new_wire.producer is component:
                new_wire.producer = optimized
            present_inputs[new_wire] = new_name

        # if there are any self-references, update them to optimized
        for name in self_references:
            optimized.inputs[name].producer = optimized

        optimized.inner_component.function = new_function

        self.optimized_components[component] = optimized
        self.in_progress.remove(component)
        return optimized

    def apply(self) -> None:
        to_visit: set[ComponentWrapper] = set(self.components)
        visited: set[ComponentWrapper] = set()
        while to_visit:
            component = to_visit.pop()
            if component in visited:
                continue
            visited.add(component)
            for input_wire in component.inputs.values():
                if isinstance(input_wire.producer, ComponentWrapper):
                    input_wire.producer = self.find_optimizations(input_wire.producer)
                    to_visit.add(input_wire.producer)


def optimize_arithmetic(wires: list[wire.Wire]) -> None:
    """
    Optimize the given components by inlining arithmetic functions where possible.

    :param wires: List of ComponentWrapper to optimize
    :return: None
    """
    optimizer = Optimizer(
        [w.producer for w in wires if isinstance(w.producer, ComponentWrapper)]
    )
    for wire_ in wires:
        if isinstance(wire_.producer, ComponentWrapper):
            wire_.producer = optimizer.find_optimizations(wire_.producer)
    optimizer.apply()
