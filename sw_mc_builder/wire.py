from __future__ import annotations

import inspect
import re
import warnings
from typing import Generic, Iterable, Literal, Optional, TypeVar, overload

from sw_mc_lib import Input, Position
from sw_mc_lib.Components import ConstantNumber, ConstantOn
from sw_mc_lib.Types import SignalType

import sw_mc_builder.components as comp
from sw_mc_builder import util

from .component_wrapper import ComponentWrapper
from .pseudo_components import (
    InputPlaceholder,
    Placeholder,
    PseudoComponent,
    Unconnected,
)

T = TypeVar("T", bound=SignalType)


class Wire(Generic[T]):
    # pylint: disable=too-many-public-methods

    SET_VIA_SET_METHOD: set[ComponentWrapper | PseudoComponent] = set()

    def __init__(
        self,
        wire_type: T,
        producer: ComponentWrapper | PseudoComponent,
        node_index: int = 0,
    ):
        self.wire_type: SignalType = wire_type
        self.producer: ComponentWrapper | PseudoComponent = producer
        self.node_index: int = node_index

    def stop_optimization(self) -> Wire[T]:
        """Will prevent the optimizer from removing this component or merging it with other components."""
        if isinstance(self.producer, ComponentWrapper):
            self.producer.optimize = False
        return self

    def force_property(self) -> Wire[T]:
        """Will overwrite the contents of a property, even if that property is already defined in a vehicle."""
        if isinstance(self.producer, ComponentWrapper):
            self.producer.force_property = True
        return self

    @staticmethod
    @overload
    def to(
        signal_type: Literal[SignalType.Number], wire: NumberInput
    ) -> NumberWire: ...

    @staticmethod
    @overload
    def to(
        signal_type: Literal[SignalType.Boolean], wire: BooleanInput
    ) -> BooleanWire: ...

    @staticmethod
    @overload
    def to(
        signal_type: Literal[SignalType.Composite], wire: CompositeInput
    ) -> CompositeWire: ...

    @staticmethod
    @overload
    def to(signal_type: Literal[SignalType.Audio], wire: AudioInput) -> AudioWire: ...

    @staticmethod
    @overload
    def to(signal_type: Literal[SignalType.Video], wire: VideoInput) -> VideoWire: ...

    @staticmethod
    def to(signal_type: SignalType, wire: Wire | int | float | bool | None) -> Wire:
        if isinstance(wire, Wire):
            if wire.wire_type != signal_type:
                raise TypeError(
                    f"Wire type mismatch: expected {signal_type}, got {wire.wire_type}"
                )
            return wire
        if signal_type == SignalType.Boolean and isinstance(wire, bool):
            if wire:
                return Wire(
                    SignalType.Boolean, ComponentWrapper(ConstantOn(1, Position()), {})
                )
            return Wire(SignalType.Boolean, Unconnected())
        if signal_type == SignalType.Number and isinstance(wire, (int, float)):
            return Wire(
                SignalType.Number,
                ComponentWrapper(ConstantNumber(0, Position(), wire), {}),
            )
        if wire is None:
            return Wire(signal_type, Unconnected())
        raise TypeError(f"Wire type mismatch: expected {signal_type}, got {wire}")

    def replace_producer(self, new_wire: Wire[T]) -> None:
        if self.wire_type != new_wire.wire_type:
            raise TypeError(
                f"Wire type mismatch: expected {self.wire_type}, got {new_wire.wire_type}"
            )
        self.producer = new_wire.producer

    @property
    def component_id(self) -> Optional[int]:
        if isinstance(self.producer, (ComponentWrapper, InputPlaceholder)):
            return self.producer.component_id
        if isinstance(self.producer, Unconnected):
            return None
        if isinstance(self.producer, Placeholder):
            raise RuntimeError(
                "Placeholder needs to be replaced before compiling microcontroller"
            )
        raise TypeError(f"Invalid producer type: {type(self.producer)}")

    def __hash__(self) -> int:
        return hash(id(self))

    def to_input(self) -> Optional[Input]:
        if self.component_id is None:
            return None
        return Input(self.component_id, node_index=self.node_index)

    def __add__(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only add NumberWire")
        return comp.add(self, other)  # type: ignore[arg-type]

    def __sub__(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only subtract NumberWire")
        return comp.sub(self, other)  # type: ignore[arg-type]

    def __mul__(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only multiply NumberWire")
        return comp.mul(self, other)  # type: ignore[arg-type]

    def __truediv__(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only divide NumberWire")
        return comp.div(self, other)[0]  # type: ignore[arg-type]

    def __mod__(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only modulo NumberWire")
        return comp.mod(self, other)  # type: ignore[arg-type]

    def __abs__(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only abs NumberWire")
        return comp.abs(self)  # type: ignore[arg-type]

    def __lshift__(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only left shift NumberWire")
        return comp.function("x*2^y", self, other)  # type: ignore[arg-type]

    def __rshift__(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only right shift NumberWire")
        return comp.function("x/2^y", self, other)  # type: ignore[arg-type]

    def __neg__(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only negate NumberWire")
        return comp.sub(comp.unconnected(SignalType.Number), self)  # type: ignore[arg-type]

    def __pow__(self, power: NumberInput, modulo: NumberInput = None) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only exponentiate NumberWire")
        if modulo is not None:
            return comp.function("(x^y)%z", self, power, modulo)  # type: ignore[arg-type]
        return comp.function("x^y", self, power)  # type: ignore[arg-type]

    @staticmethod
    def __slice_to_range(s: object) -> list[int]:
        if isinstance(s, slice):
            start = s.start if s.start is not None else 1
            stop = s.stop if s.stop is not None else 32
            step = s.step if s.step is not None else 1
            if not (1 <= start <= 32 and 1 <= stop <= 32):
                raise ValueError("Slice indices must be in the range [1,32]")
            if step == 0:
                raise ValueError("Slice step cannot be zero")
            return list(range(start, stop + 1, step))
        if isinstance(s, int):
            if not 1 <= s <= 32:
                raise ValueError("Index must be in the range [1,32]")
            return [s]
        raise TypeError("Index must be an integer or slice")

    @overload
    def __getitem__(self, item: int) -> NumberWire: ...

    @overload
    def __getitem__(self, item: slice) -> list[NumberWire]: ...

    def __getitem__(self, item: int | slice) -> NumberWire | list[NumberWire]:
        if self.wire_type != SignalType.Composite:
            raise TypeError("Can only index CompositeWire")
        index_slice = self.__slice_to_range(item)
        if isinstance(item, slice):
            return [
                comp.composite_read_number(self, idx)  # type: ignore[arg-type]
                for idx in index_slice
            ]
        return comp.composite_read_number(self, item)  # type: ignore[arg-type]

    @overload
    def get_bool(self, item: int) -> BooleanWire: ...

    @overload
    def get_bool(self, item: slice) -> list[BooleanWire]: ...

    def get_bool(self, item: int | slice) -> BooleanWire | list[BooleanWire]:
        if self.wire_type != SignalType.Composite:
            raise TypeError("Can only index CompositeWire")
        index_slice = self.__slice_to_range(item)
        if isinstance(item, slice):
            return [
                comp.composite_read_boolean(self, idx)  # type: ignore[arg-type]
                for idx in index_slice
            ]
        return comp.composite_read_boolean(self, item)  # type: ignore[arg-type]

    @staticmethod
    def __is_bool(element: object) -> bool:
        return isinstance(element, bool) or (
            isinstance(element, Wire) and element.wire_type == SignalType.Boolean
        )

    @staticmethod
    def __is_number(element: object) -> bool:
        return isinstance(element, (int, float)) or (
            isinstance(element, Wire) and element.wire_type == SignalType.Number
        )

    @overload
    def set(self, item: int, value: NumberInput | BooleanInput) -> CompositeWire: ...

    @overload
    def set(
        self, item: slice, value: Iterable[NumberWire | int | float]
    ) -> CompositeWire: ...

    @overload
    def set(
        self, item: slice, value: Iterable[BooleanWire | bool]
    ) -> CompositeWire: ...

    def set(
        self,
        item: int | slice,
        value: (
            NumberInput
            | BooleanInput
            | Iterable[NumberWire | int | float]
            | Iterable[BooleanWire | bool]
        ),
    ) -> CompositeWire:
        """Alias for __setitem__ to allow using .set() instead of []= for setting composite values."""
        self.SET_VIA_SET_METHOD.add(self.producer)
        if self.wire_type != SignalType.Composite:
            raise TypeError("Can only index CompositeWire")
        index_slice = self.__slice_to_range(item)
        if isinstance(item, slice):
            if not isinstance(value, Iterable):
                raise TypeError("Value must be an iterable when using slice assignment")
            value_list = list(value)
            if len(value_list) != len(index_slice):
                raise ValueError("Value length must match slice length")
            if len(index_slice) == 0:
                return self  # type: ignore[return-value]
            composite_write = (
                comp.composite_write_number
                if self.__is_number(value_list[0])
                else comp.composite_write_boolean
            )
            return composite_write(self, **{f"channel{idx}": val for idx, val in zip(index_slice, value_list)})  # type: ignore[arg-type]
        if self.__is_number(value):
            return comp.composite_write_number(self, item, value)  # type: ignore[arg-type]
        if self.__is_bool(value):
            return comp.composite_write_boolean(self, item, value)  # type: ignore[arg-type]
        raise TypeError("Can only write NumberWire or BooleanWire to CompositeWire")

    @overload
    def __setitem__(self, item: int, value: NumberInput | BooleanInput) -> None: ...

    @overload
    def __setitem__(
        self, item: slice, value: Iterable[NumberWire | int | float]
    ) -> None: ...

    @overload
    def __setitem__(self, item: slice, value: Iterable[BooleanWire | bool]) -> None: ...

    def __setitem__(
        self,
        item: int | slice,
        value: (
            NumberInput
            | BooleanInput
            | Iterable[NumberWire | int | float]
            | Iterable[BooleanWire | bool]
        ),
    ) -> None:
        if self.producer in self.SET_VIA_SET_METHOD:
            warnings.warn(
                "Using both `wire[index] = value` and `wire.set(index, value)` on the same CompositeWire is not recommended. This may lead to surprising behaviour.",
                stacklevel=2,
            )
            stack = inspect.stack()
            if len(stack) > 1:
                frame_info = stack[1]
                context = frame_info.code_context
                index = frame_info.index
                if context is not None and index is not None:
                    recommendation = re.sub(
                        r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*\[([^]]+)]\s*=\s*(.*)$",
                        r"\1 = \1.set(\2, \3)",
                        context[index],
                    )
                    if recommendation != context[index]:
                        print(f"Recommended replacement:\n  {recommendation.strip()}")
        clone = Wire(self.wire_type, self.producer, self.node_index)
        self.replace_producer(clone.set(item, value))  # type: ignore[arg-type]

    def __eq__(self, other: object) -> BooleanWire:  # type: ignore[override]
        if not isinstance(other, (Wire, int, float)):
            return NotImplemented
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only compare NumberWire")
        return comp.equal(self, other)  # type: ignore[arg-type]

    def __ne__(self, other: object) -> BooleanWire:  # type: ignore[override]
        if not isinstance(other, (Wire, int, float)):
            return NotImplemented
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only compare NumberWire")
        return comp.not_(comp.equal(self, other))  # type: ignore[arg-type]

    def __lt__(self, other: NumberInput) -> BooleanWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only compare NumberWire")
        return comp.less_than(self, other)  # type: ignore[arg-type]

    def __le__(self, other: NumberInput) -> BooleanWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only compare NumberWire")
        return comp.or_(comp.less_than(self, other), comp.equal(self, other))  # type: ignore[arg-type]

    def __gt__(self, other: NumberInput) -> BooleanWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only compare NumberWire")
        return comp.greater_than(self, other)  # type: ignore[arg-type]

    def __ge__(self, other: NumberInput) -> BooleanWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only compare NumberWire")
        return comp.or_(comp.greater_than(self, other), comp.equal(self, other))  # type: ignore[arg-type]

    def __and__(self, other: BooleanInput) -> BooleanWire:
        if self.wire_type != SignalType.Boolean:
            raise TypeError("Can only AND BooleanWire")
        return comp.and_(self, other)  # type: ignore[arg-type]

    def __or__(self, other: BooleanInput) -> BooleanWire:
        if self.wire_type != SignalType.Boolean:
            raise TypeError("Can only OR BooleanWire")
        return comp.or_(self, other)  # type: ignore[arg-type]

    def __invert__(self) -> BooleanWire:
        if self.wire_type != SignalType.Boolean:
            raise TypeError("Can only NOT BooleanWire")
        return comp.not_(self)  # type: ignore[arg-type]

    def int(self) -> NumberWire:
        if self.wire_type not in (SignalType.Number, SignalType.Boolean):
            raise TypeError("Can only convert NumberWire or BooleanWire to int")
        if self.wire_type == SignalType.Boolean:
            return util.bool_to_int(self)  # type: ignore[arg-type]
        return self  # type: ignore[return-value]

    def max(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only max NumberWire")
        return comp.function("max(x,y)", self, other)  # type: ignore[arg-type]

    def min(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only min NumberWire")
        return comp.function("min(x,y)", self, other)  # type: ignore[arg-type]

    def clamp(self, min_: NumberInput, max_: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only clamp NumberWire")
        return comp.function("clamp(x,y,z)", self, min_, max_)  # type: ignore[arg-type]

    def lerp(self, a: NumberInput, b: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only lerp NumberWire")
        return comp.function("lerp(x,y,z)", self, a, b)  # type: ignore[arg-type]

    def sin(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only sin NumberWire")
        return comp.function("sin(x)", self)  # type: ignore[arg-type]

    def cos(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only cos NumberWire")
        return comp.function("cos(x)", self)  # type: ignore[arg-type]

    def tan(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only tan NumberWire")
        return comp.function("tan(x)", self)  # type: ignore[arg-type]

    def asin(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only asin NumberWire")
        return comp.function("asin(x)", self)  # type: ignore[arg-type]

    def acos(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only acos NumberWire")
        return comp.function("acos(x)", self)  # type: ignore[arg-type]

    def atan(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only atan NumberWire")
        return comp.function("atan(x)", self)  # type: ignore[arg-type]

    def atan2(self, other: NumberInput) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only atan2 NumberWire")
        return comp.function("atan2(x,y)", self, other)  # type: ignore[arg-type]

    def ceil(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only ceil NumberWire")
        return comp.function("ceil(x)", self)  # type: ignore[arg-type]

    def floor(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only floor NumberWire")
        return comp.function("floor(x)", self)  # type: ignore[arg-type]

    def round(self, ndigits: NumberInput = 0) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only round NumberWire")
        return comp.function("round(x,y)", self, ndigits)  # type: ignore[arg-type]

    def sgn(self) -> NumberWire:
        """Sign function: -1 if x < 0, 1 if x == 0, 1 if x > 0"""
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only sgn NumberWire")
        return comp.function("sgn(x)", self)  # type: ignore[arg-type]

    def sqrt(self) -> NumberWire:
        if self.wire_type != SignalType.Number:
            raise TypeError("Can only sqrt NumberWire")
        return comp.function("sqrt(x)", self)  # type: ignore[arg-type]

    @overload
    def switch(self, on_value: NumberInput, off_value: NumberInput) -> NumberWire: ...  # type: ignore[overload-overlap]

    @overload
    def switch(  # type: ignore[overload-overlap]
        self, on_value: BooleanInput, off_value: BooleanInput
    ) -> BooleanWire: ...

    @overload
    def switch(  # type: ignore[overload-overlap]
        self, on_value: CompositeInput, off_value: CompositeInput
    ) -> CompositeWire: ...

    @overload
    def switch(self, on_value: AudioInput, off_value: AudioInput) -> AudioWire: ...  # type: ignore[overload-overlap]

    @overload
    def switch(self, on_value: VideoInput, off_value: VideoInput) -> VideoWire: ...

    def switch(
        self,
        on_value: NumberInput | BooleanInput | CompositeInput | AudioInput | VideoInput,
        off_value: (
            NumberInput | BooleanInput | CompositeInput | AudioInput | VideoInput
        ),
    ) -> NumberWire | BooleanWire | CompositeWire | AudioWire | VideoWire:
        if self.wire_type != SignalType.Boolean:
            raise TypeError("Can only switch BooleanWire")
        if self.__is_number(on_value):
            return comp.numerical_switchbox(on_value, off_value, self)  # type: ignore[arg-type]
        if self.__is_bool(on_value):
            return comp.composite_switchbox(on_value, off_value, self)  # type: ignore[arg-type]
        assert isinstance(on_value, Wire)
        if on_value.wire_type == SignalType.Audio:
            return comp.audio_switchbox(on_value, off_value, self)  # type: ignore[arg-type]
        if on_value.wire_type == SignalType.Video:
            return comp.video_switchbox(on_value, off_value, self)  # type: ignore[arg-type]
        if on_value.wire_type == SignalType.Boolean:
            return comp.or_(comp.and_(self, on_value), comp.and_(comp.not_(self), off_value))  # type: ignore[arg-type]
        raise NotImplementedError("Switch on not implemented")


NumberWire = Wire[Literal[SignalType.Number]]
BooleanWire = Wire[Literal[SignalType.Boolean]]
CompositeWire = Wire[Literal[SignalType.Composite]]
AudioWire = Wire[Literal[SignalType.Audio]]
VideoWire = Wire[Literal[SignalType.Video]]

NumberInput = Wire[Literal[SignalType.Number]] | int | float | None
BooleanInput = Wire[Literal[SignalType.Boolean]] | bool | None
CompositeInput = Wire[Literal[SignalType.Composite]] | None
AudioInput = Wire[Literal[SignalType.Audio]] | None
VideoInput = Wire[Literal[SignalType.Video]] | None
