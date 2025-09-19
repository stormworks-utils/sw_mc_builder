# pylint: disable=too-many-lines, too-many-arguments, too-many-locals, redefined-outer-name
from typing import Optional

from sw_mc_lib import Position
from sw_mc_lib.Components import *
from sw_mc_lib.Components.property_dropdown import DropDownOption
from sw_mc_lib.Types import PulseMode, SignalType, TimerUnit

from sw_mc_builder import script_handling

from .component_wrapper import ComponentWrapper
from .pseudo_components import InputPlaceholder, Placeholder, Unconnected
from .wire import (
    AudioInput,
    AudioWire,
    BooleanInput,
    BooleanWire,
    CompositeInput,
    CompositeWire,
    NumberInput,
    NumberWire,
    VideoInput,
    VideoWire,
    Wire,
)

Number = float | int


def input(
    signal_type: SignalType,
    name: str,
    description: str = "The input signal to be processed.",
) -> Wire:
    """An input node for the microcontroller. This represents an input from the vehicle."""
    return Wire(signal_type, InputPlaceholder(-1, name, description), 0)


def add(a: NumberInput, b: NumberInput) -> NumberWire:
    """Adds the two input values together and outputs the result."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            Add(0, Position()),
            {
                "a_input": Wire.to(SignalType.Number, a),
                "b_input": Wire.to(SignalType.Number, b),
            },
        ),
    )


def sub(a: NumberInput, b: NumberInput) -> NumberWire:
    """Subtracts the second input from the first and outputs the result."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            Subtract(0, Position()),
            {
                "a_input": Wire.to(SignalType.Number, a),
                "b_input": Wire.to(SignalType.Number, b),
            },
        ),
    )


def mul(a: NumberInput, b: NumberInput) -> NumberWire:
    """Multiplies the two input values and outputs the result."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            Multiply(0, Position()),
            {
                "a_input": Wire.to(SignalType.Number, a),
                "b_input": Wire.to(SignalType.Number, b),
            },
        ),
    )


def div(a: NumberInput, b: NumberInput) -> tuple[NumberWire, BooleanWire]:
    """Divides the first input by the second and outputs the result. Also outputs, if the division was divieded by zero."""
    comp = ComponentWrapper(
        Divide(0, Position()),
        {
            "a_input": Wire.to(SignalType.Number, a),
            "b_input": Wire.to(SignalType.Number, b),
        },
    )
    return Wire(SignalType.Number, comp), Wire(SignalType.Boolean, comp, node_index=1)


def mod(a: NumberInput, b: NumberInput) -> NumberWire:
    """Outputs the modulo of input A by input B."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            Modulo(0, Position()),
            {
                "a_input": Wire.to(SignalType.Number, a),
                "b_input": Wire.to(SignalType.Number, b),
            },
        ),
    )


def abs(a: NumberInput) -> NumberWire:
    """Outputs the absolute value of the input value (negative numbers become positive)."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            Abs(0, Position()),
            {"number_input": Wire.to(SignalType.Number, a)},
        ),
    )


def clamp(a: NumberInput, min_value: Number, max_value: Number) -> NumberWire:
    """Clamps the input value between a set min and max and outputs the result."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            Clamp(0, Position(), min_value, max_value),
            {"number_input": Wire.to(SignalType.Number, a)},
        ),
    )


def constant_number(value: Number) -> NumberWire:
    """Outputs a constant number that is set as property."""
    return Wire(
        SignalType.Number, ComponentWrapper(ConstantNumber(0, Position(), value), {})
    )


def delta(value: NumberInput) -> NumberWire:
    """Delta Of Input Value. Outputs the difference between the current and previous input value."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            Delta(0, Position()),
            {"value_input": Wire.to(SignalType.Number, value)},
        ),
    )


def equal(
    a: NumberInput = None, b: NumberInput = None, epsilon: Optional[Number] = None
) -> BooleanWire:
    """Compares whether or not two numbers are equal within a set accuracy."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            Equal(0, Position(), epsilon_property=epsilon),
            {
                "a_input": Wire.to(SignalType.Number, a),
                "b_input": Wire.to(SignalType.Number, b),
            },
        ),
    )


def function(
    function_string: str,
    x: NumberInput = None,
    y: NumberInput = None,
    z: NumberInput = None,
    w: NumberInput = None,
    a: NumberInput = None,
    b: NumberInput = None,
    c: NumberInput = None,
    d: NumberInput = None,
) -> NumberWire:
    """Evaluates a mathematical expression with up to 8 input variables and outputs the result."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            ArithmeticFunction8In(0, Position(), function_string),
            {
                "x_input": Wire.to(SignalType.Number, x),
                "y_input": Wire.to(SignalType.Number, y),
                "z_input": Wire.to(SignalType.Number, z),
                "w_input": Wire.to(SignalType.Number, w),
                "a_input": Wire.to(SignalType.Number, a),
                "b_input": Wire.to(SignalType.Number, b),
                "c_input": Wire.to(SignalType.Number, c),
                "d_input": Wire.to(SignalType.Number, d),
            },
        ),
    )


def unconnected(signal_type: SignalType) -> Wire:
    """
    Unconnected component for unused inputs. Does not have to be resolved to generate a valid microcontroller.
    """
    return Wire(signal_type, Unconnected())


def placeholder(signal_type: SignalType) -> Wire:
    """
    Placeholder component for incomplete circuits.
    Can be used for circular dependencies.
    Must be resolved to generate a valid microcontroller.
    """
    return Wire(signal_type, Placeholder())


def and_(a: BooleanInput, b: BooleanInput) -> BooleanWire:
    """Outputs the logical AND of its two input signals."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            AND(0, Position()),
            {
                "a_input": Wire.to(SignalType.Boolean, a),
                "b_input": Wire.to(SignalType.Boolean, b),
            },
        ),
    )


def or_(a: BooleanInput, b: BooleanInput) -> BooleanWire:
    """Outputs the logical OR of its two input signals."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            OR(0, Position()),
            {
                "a_input": Wire.to(SignalType.Boolean, a),
                "b_input": Wire.to(SignalType.Boolean, b),
            },
        ),
    )


def xor(a: BooleanInput, b: BooleanInput) -> BooleanWire:
    """Outputs the logical XOR of its two input signals."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            XOR(0, Position()),
            {
                "a_input": Wire.to(SignalType.Boolean, a),
                "b_input": Wire.to(SignalType.Boolean, b),
            },
        ),
    )


def nand(a: BooleanInput, b: BooleanInput) -> BooleanWire:
    """Outputs the logical NAND of its two input signals."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            NAND(0, Position()),
            {
                "a_input": Wire.to(SignalType.Boolean, a),
                "b_input": Wire.to(SignalType.Boolean, b),
            },
        ),
    )


def nor(a: BooleanInput, b: BooleanInput) -> BooleanWire:
    """Outputs the logical NOR of its two input signals."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            NOR(0, Position()),
            {
                "a_input": Wire.to(SignalType.Boolean, a),
                "b_input": Wire.to(SignalType.Boolean, b),
            },
        ),
    )


def not_(a: BooleanInput) -> BooleanWire:
    """Outputs the logical NOT of its input signal."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            NOT(0, Position()),
            {
                "a_input": Wire.to(SignalType.Boolean, a),
            },
        ),
    )


def constant_on() -> BooleanWire:
    """Outputs a constant on signal."""
    return Wire(SignalType.Boolean, ComponentWrapper(ConstantOn(0, Position()), {}))


def jk_flip_flop(
    set_: BooleanInput = None, reset: BooleanInput = None
) -> tuple[BooleanWire, BooleanWire]:
    """
    An JK flip flop that can be set and reset using two on/off inputs.
    Returns (Q, not Q).
    """
    component = ComponentWrapper(
        JKFlipFlop(0, Position()),
        {
            "set_input": Wire.to(SignalType.Boolean, set_),
            "reset_input": Wire.to(SignalType.Boolean, reset),
        },
    )
    return Wire(SignalType.Boolean, component), Wire(
        SignalType.Boolean, component, node_index=1
    )


def sr_latch(
    set_: BooleanInput = None, reset: BooleanInput = None
) -> tuple[BooleanWire, BooleanWire]:
    """
    An SR latch that can be set and reset using two on/off inputs.
    Returns (Q, not Q).
    """
    component = ComponentWrapper(
        SRLatch(0, Position()),
        {
            "set_input": Wire.to(SignalType.Boolean, set_),
            "reset_input": Wire.to(SignalType.Boolean, reset),
        },
    )
    return Wire(SignalType.Boolean, component), Wire(
        SignalType.Boolean, component, node_index=1
    )


def boolean_function(
    function_string: str,
    x: BooleanInput = None,
    y: BooleanInput = None,
    z: BooleanInput = None,
    w: BooleanInput = None,
    a: BooleanInput = None,
    b: BooleanInput = None,
    c: BooleanInput = None,
    d: BooleanInput = None,
) -> BooleanWire:
    """Evaluates a logical expression with up to 8 input variables and outputs the result."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            BooleanFunction8In(0, Position(), function_string),
            {
                "x_input": Wire.to(SignalType.Boolean, x),
                "y_input": Wire.to(SignalType.Boolean, y),
                "z_input": Wire.to(SignalType.Boolean, z),
                "w_input": Wire.to(SignalType.Boolean, w),
                "a_input": Wire.to(SignalType.Boolean, a),
                "b_input": Wire.to(SignalType.Boolean, b),
                "c_input": Wire.to(SignalType.Boolean, c),
                "d_input": Wire.to(SignalType.Boolean, d),
            },
        ),
    )


def pulse(
    toggle: BooleanInput = None, mode: PulseMode = PulseMode.OffToOn
) -> BooleanWire:
    """
    A switch that outputs a single tick pulse.
    It can be configured to pulse when being switched from off to on (default), on to off,
    or always when the input signal changes.
    """
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            Pulse(0, Position(), mode_property=mode),
            {"toggle_signal_input": Wire.to(SignalType.Boolean, toggle)},
        ),
    )


def push_to_toggle(toggle_signal: BooleanInput = None) -> BooleanWire:
    """An on/off switch that is toggled every time a new on signal is sent to its input."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            PushToToggle(0, Position()),
            {"a_input": Wire.to(SignalType.Boolean, toggle_signal)},
        ),
    )


def blinker(
    control_signal: BooleanInput = None,
    blink_on_duration: Number = 1.0,
    blink_off_duration: Number = 1.0,
) -> BooleanWire:
    """Outputs a value that blinks between on and off at a set rate."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            Blinker(0, Position(), None, blink_on_duration, blink_off_duration),
            {"control_signal_input": Wire.to(SignalType.Boolean, control_signal)},
        ),
    )


def capacitor(
    charge: BooleanInput = None, charge_time: Number = 1.0, discharge_time: Number = 1.0
) -> BooleanWire:
    """Charges up when receiving an on signal, then discharges over a period of time."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            Capacitor(0, Position(), None, charge_time, discharge_time),
            {"charge_input": Wire.to(SignalType.Boolean, charge)},
        ),
    )


def greater_than(a: NumberInput = None, b: NumberInput = None) -> BooleanWire:
    """Outputs an on signal if the first input is greater than the second."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            GreaterThan(0, Position()),
            {
                "a_input": Wire.to(SignalType.Number, a),
                "b_input": Wire.to(SignalType.Number, b),
            },
        ),
    )


def less_than(a: NumberInput = None, b: NumberInput = None) -> BooleanWire:
    """Outputs an on signal if the first input is less than the second."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            LessThan(0, Position()),
            {
                "a_input": Wire.to(SignalType.Number, a),
                "b_input": Wire.to(SignalType.Number, b),
            },
        ),
    )


def memory_register(
    set_: BooleanInput = None,
    reset: BooleanInput = None,
    data: NumberInput = None,
    reset_value: Number = 0,
) -> NumberWire:
    """
    Remembers the input value when receiving a signal to the Set node.
    When the Reset node receives a signal, the stored number is cleared to a value that can be customised in the property.
    """
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            MemoryRegister(0, Position(), reset_value),
            {
                "set_input": Wire.to(SignalType.Boolean, set_),
                "reset_input": Wire.to(SignalType.Boolean, reset),
                "number_to_store_input": Wire.to(SignalType.Number, data),
            },
        ),
    )


def numerical_junction(
    value: NumberInput = None, switch: BooleanInput = None
) -> tuple[NumberWire, NumberWire]:
    """
    Outputs the input number to one of the outputs depending on whether or not the Switch Signal is on.
    The path that the input doesn't take will output a value of 0.
    """
    component = ComponentWrapper(
        NumericalJunction(0, Position()),
        {
            "value_to_pass_through_input": Wire.to(SignalType.Number, value),
            "switch_signal_input": Wire.to(SignalType.Boolean, switch),
        },
    )
    return Wire(SignalType.Number, component), Wire(
        SignalType.Number, component, node_index=1
    )


def numerical_switchbox(
    on_value: NumberInput = None,
    off_value: NumberInput = None,
    switch: BooleanInput = None,
) -> NumberWire:
    """
    Outputs the first input value when receiving an on signal, and the second when receiving an off signal.
    """
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            NumericalSwitchbox(0, Position()),
            {
                "on_value_input": Wire.to(SignalType.Number, on_value),
                "off_value_input": Wire.to(SignalType.Number, off_value),
                "switch_signal_input": Wire.to(SignalType.Boolean, switch),
            },
        ),
    )


def pid(
    setpoint: NumberInput = None,
    process_variable: NumberInput = None,
    active: BooleanInput = None,
    kp: Number = 0.0,
    ki: Number = 0.0,
    kd: Number = 0.0,
) -> NumberWire:
    """
    A basic PID controller. The proportional, integral and derivative gains can be set using properties.
    """
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            PIDController(
                0,
                Position(),
                proportional_property=kp,
                integral_property=ki,
                derivative_property=kd,
            ),
            {
                "setpoint_input": Wire.to(SignalType.Number, setpoint),
                "process_variable_input": Wire.to(SignalType.Number, process_variable),
                "active_input": Wire.to(SignalType.Boolean, active),
            },
        ),
    )


def advanced_pid(
    setpoint: NumberInput = None,
    process_variable: NumberInput = None,
    proportional_gain: NumberInput = None,
    integral_gain: NumberInput = None,
    derivative_gain: NumberInput = None,
    active: BooleanInput = None,
) -> NumberWire:
    """
    A PID controller with variable proportional, integral and derivative gains.
    """
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            PIDControllerAdvanced(0, Position()),
            {
                "setpoint_input": Wire.to(SignalType.Number, setpoint),
                "process_variable_input": Wire.to(SignalType.Number, process_variable),
                "proportional_input": Wire.to(SignalType.Number, proportional_gain),
                "integral_input": Wire.to(SignalType.Number, integral_gain),
                "derivative_input": Wire.to(SignalType.Number, derivative_gain),
                "active_input": Wire.to(SignalType.Boolean, active),
            },
        ),
    )


def threshold(
    value: NumberInput = None,
    low_threshold: Number = 0.0,
    high_threshold: Number = 1.0,
) -> BooleanWire:
    """Outputs an on/off signal indicating whether or not the input value is within a set threshold."""
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            Threshold(0, Position(), low_threshold, high_threshold),
            {
                "number_input": Wire.to(SignalType.Number, value),
            },
        ),
    )


def timer_rtf(
    enable: BooleanInput = None,
    duration: NumberInput = None,
    reset: BooleanInput = None,
    duration_unit: TimerUnit = TimerUnit.Seconds,
) -> BooleanWire:
    """
    Variable input timer. Outputs an on signal when the timer is less than its duration. The timer will not reset until it is signalled.
    """
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            TimerRTF(0, Position(), duration_unit),
            {
                "timer_enable_input": Wire.to(SignalType.Boolean, enable),
                "duration_input": Wire.to(SignalType.Number, duration),
                "reset_input": Wire.to(SignalType.Boolean, reset),
            },
        ),
    )


def timer_rto(
    enable: BooleanInput = None,
    duration: NumberInput = None,
    reset: BooleanInput = None,
    duration_unit: TimerUnit = TimerUnit.Seconds,
) -> BooleanWire:
    """
    Variable input timer. Outputs an on signal when the timer reaches its duration. The timer will not reset until it is signalled.
    """
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            TimerRTO(0, Position(), duration_unit),
            {
                "timer_enable_input": Wire.to(SignalType.Boolean, enable),
                "duration_input": Wire.to(SignalType.Number, duration),
                "reset_input": Wire.to(SignalType.Boolean, reset),
            },
        ),
    )


def timer_tof(
    enable: BooleanInput = None,
    duration: NumberInput = None,
    duration_unit: TimerUnit = TimerUnit.Seconds,
) -> BooleanWire:
    """
    Variable input timer. Outputs an on signal when the timer is less than its duration. The timer will reset when off.
    """
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            TimerTOF(0, Position(), duration_unit),
            {
                "timer_enable_input": Wire.to(SignalType.Boolean, enable),
                "duration_input": Wire.to(SignalType.Number, duration),
            },
        ),
    )


def timer_ton(
    enable: BooleanInput = None,
    duration: NumberInput = None,
    duration_unit: TimerUnit = TimerUnit.Seconds,
) -> BooleanWire:
    """
    Variable input timer. Outputs an on signal when the timer reaches its duration. The timer will reset when off.
    """
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            TimerTON(0, Position(), duration_unit),
            {
                "timer_enable_input": Wire.to(SignalType.Boolean, enable),
                "duration_input": Wire.to(SignalType.Number, duration),
            },
        ),
    )


def up_down_counter(
    up: BooleanInput = None,
    down: BooleanInput = None,
    reset: BooleanInput = None,
    increment: Number = 1,
    reset_value: Number = 0,
    min_value: Number = 0,
    max_value: Number = 0,
    clamp: bool = False,
) -> NumberWire:
    """Has an internal value that will increase and decrease when receiving different signals."""
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            UpDownCounter(
                0,
                Position(),
                min_property=min_value,
                max_property=max_value,
                clamp=clamp,
                increment_property=increment,
                reset_property=reset_value,
            ),
            {
                "up_input": Wire.to(SignalType.Boolean, up),
                "down_input": Wire.to(SignalType.Boolean, down),
                "reset_input": Wire.to(SignalType.Boolean, reset),
            },
        ),
    )


def audio_switchbox(
    on_value: AudioInput = None,
    off_value: AudioInput = None,
    switch: BooleanInput = None,
) -> AudioWire:
    """
    Outputs the first input audio when receiving an on signal, and the second when receiving an off signal.
    """
    return Wire(
        SignalType.Audio,
        ComponentWrapper(
            AudioSwitchbox(0, Position()),
            {
                "on_value_input": Wire.to(SignalType.Audio, on_value),
                "off_value_input": Wire.to(SignalType.Audio, off_value),
                "switch_signal_input": Wire.to(SignalType.Boolean, switch),
            },
        ),
    )


def composite_switchbox(
    on_value: CompositeInput = None,
    off_value: CompositeInput = None,
    switch: BooleanInput = None,
) -> CompositeWire:
    """
    Outputs the first input composite when receiving an on signal, and the second when receiving an off signal.
    """
    return Wire(
        SignalType.Composite,
        ComponentWrapper(
            CompositeSwitchbox(0, Position()),
            {
                "on_value_input": Wire.to(SignalType.Composite, on_value),
                "off_value_input": Wire.to(SignalType.Composite, off_value),
                "switch_signal_input": Wire.to(SignalType.Boolean, switch),
            },
        ),
    )


def video_switchbox(
    on_value: VideoInput = None,
    off_value: VideoInput = None,
    switch: BooleanInput = None,
) -> VideoWire:
    """
    Outputs the first input video when receiving an on signal, and the second when receiving an off signal.
    """
    return Wire(
        SignalType.Video,
        ComponentWrapper(
            VideoSwitchbox(0, Position()),
            {
                "on_value_input": Wire.to(SignalType.Video, on_value),
                "off_value_input": Wire.to(SignalType.Video, off_value),
                "switch_signal_input": Wire.to(SignalType.Boolean, switch),
            },
        ),
    )


def composite_binary_to_number(value: CompositeInput = None) -> NumberWire:
    """
    Reads the on/off signals of a composite link and encodes them in the bits of an output number.
    """
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            CompositeBinaryToNumber(0, Position()),
            {"signal_to_convert_input": Wire.to(SignalType.Composite, value)},
        ),
    )


def number_to_composite_binary(value: NumberInput = None) -> CompositeWire:
    """
    Converts a number (rounded) to binary and outputs the bits as composite on/off signals.
    """
    return Wire(
        SignalType.Composite,
        ComponentWrapper(
            NumberToCompositeBinary(0, Position()),
            {"number_to_convert_input": Wire.to(SignalType.Number, value)},
        ),
    )


def composite_read_number(
    composite: CompositeInput = None,
    channel: int = 1,
    dynamic_channel: NumberInput = None,
) -> NumberWire:
    """
    Reads the number value from a selected channel of a composite input.
    If channel is 0, will read from the channel specified by the dynamic channel input.
    """
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            CompositeReadNumber(
                0, Position(), channel if dynamic_channel is None else 0
            ),
            {
                "composite_signal_input": Wire.to(SignalType.Composite, composite),
                "start_channel_input": Wire.to(SignalType.Number, dynamic_channel),
            },
        ),
    )


def composite_read_boolean(
    composite: CompositeInput = None,
    channel: int = 1,
    dynamic_channel: NumberInput = None,
) -> BooleanWire:
    """
    Reads the on/off value from a selected channel of a composite input.
    If channel is 0, will read from the channel specified by the dynamic channel input.
    """
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            CompositeReadBoolean(
                0, Position(), channel if dynamic_channel is None else 0
            ),
            {
                "composite_signal_input": Wire.to(SignalType.Composite, composite),
                "start_channel_input": Wire.to(SignalType.Number, dynamic_channel),
            },
        ),
    )


def composite_write_number(
    composite: CompositeInput = None,
    channel1: NumberInput = None,
    channel2: NumberInput = None,
    channel3: NumberInput = None,
    channel4: NumberInput = None,
    channel5: NumberInput = None,
    channel6: NumberInput = None,
    channel7: NumberInput = None,
    channel8: NumberInput = None,
    channel9: NumberInput = None,
    channel10: NumberInput = None,
    channel11: NumberInput = None,
    channel12: NumberInput = None,
    channel13: NumberInput = None,
    channel14: NumberInput = None,
    channel15: NumberInput = None,
    channel16: NumberInput = None,
    channel17: NumberInput = None,
    channel18: NumberInput = None,
    channel19: NumberInput = None,
    channel20: NumberInput = None,
    channel21: NumberInput = None,
    channel22: NumberInput = None,
    channel23: NumberInput = None,
    channel24: NumberInput = None,
    channel25: NumberInput = None,
    channel26: NumberInput = None,
    channel27: NumberInput = None,
    channel28: NumberInput = None,
    channel29: NumberInput = None,
    channel30: NumberInput = None,
    channel31: NumberInput = None,
    channel32: NumberInput = None,
    dynamic_channel: NumberInput = None,
) -> CompositeWire:
    """
    Outputs a composite signal that is the same as the input composite, but with one channel replaced by a number value.
    If channel is 0, will write to the channel specified by the dynamic channel input.
    """
    return Wire(
        SignalType.Composite,
        ComponentWrapper(
            CompositeWriteNumber(
                0, Position(), 1 if dynamic_channel is None else 0, 32
            ),
            {
                "composite_signal_input": Wire.to(SignalType.Composite, composite),
                "start_channel_input": Wire.to(SignalType.Number, dynamic_channel),
                "channel_1_input": Wire.to(SignalType.Number, channel1),
                "channel_2_input": Wire.to(SignalType.Number, channel2),
                "channel_3_input": Wire.to(SignalType.Number, channel3),
                "channel_4_input": Wire.to(SignalType.Number, channel4),
                "channel_5_input": Wire.to(SignalType.Number, channel5),
                "channel_6_input": Wire.to(SignalType.Number, channel6),
                "channel_7_input": Wire.to(SignalType.Number, channel7),
                "channel_8_input": Wire.to(SignalType.Number, channel8),
                "channel_9_input": Wire.to(SignalType.Number, channel9),
                "channel_10_input": Wire.to(SignalType.Number, channel10),
                "channel_11_input": Wire.to(SignalType.Number, channel11),
                "channel_12_input": Wire.to(SignalType.Number, channel12),
                "channel_13_input": Wire.to(SignalType.Number, channel13),
                "channel_14_input": Wire.to(SignalType.Number, channel14),
                "channel_15_input": Wire.to(SignalType.Number, channel15),
                "channel_16_input": Wire.to(SignalType.Number, channel16),
                "channel_17_input": Wire.to(SignalType.Number, channel17),
                "channel_18_input": Wire.to(SignalType.Number, channel18),
                "channel_19_input": Wire.to(SignalType.Number, channel19),
                "channel_20_input": Wire.to(SignalType.Number, channel20),
                "channel_21_input": Wire.to(SignalType.Number, channel21),
                "channel_22_input": Wire.to(SignalType.Number, channel22),
                "channel_23_input": Wire.to(SignalType.Number, channel23),
                "channel_24_input": Wire.to(SignalType.Number, channel24),
                "channel_25_input": Wire.to(SignalType.Number, channel25),
                "channel_26_input": Wire.to(SignalType.Number, channel26),
                "channel_27_input": Wire.to(SignalType.Number, channel27),
                "channel_28_input": Wire.to(SignalType.Number, channel28),
                "channel_29_input": Wire.to(SignalType.Number, channel29),
                "channel_30_input": Wire.to(SignalType.Number, channel30),
                "channel_31_input": Wire.to(SignalType.Number, channel31),
                "channel_32_input": Wire.to(SignalType.Number, channel32),
            },
        ),
    )


def composite_write_boolean(
    composite: CompositeInput = None,
    channel1: BooleanInput = None,
    channel2: BooleanInput = None,
    channel3: BooleanInput = None,
    channel4: BooleanInput = None,
    channel5: BooleanInput = None,
    channel6: BooleanInput = None,
    channel7: BooleanInput = None,
    channel8: BooleanInput = None,
    channel9: BooleanInput = None,
    channel10: BooleanInput = None,
    channel11: BooleanInput = None,
    channel12: BooleanInput = None,
    channel13: BooleanInput = None,
    channel14: BooleanInput = None,
    channel15: BooleanInput = None,
    channel16: BooleanInput = None,
    channel17: BooleanInput = None,
    channel18: BooleanInput = None,
    channel19: BooleanInput = None,
    channel20: BooleanInput = None,
    channel21: BooleanInput = None,
    channel22: BooleanInput = None,
    channel23: BooleanInput = None,
    channel24: BooleanInput = None,
    channel25: BooleanInput = None,
    channel26: BooleanInput = None,
    channel27: BooleanInput = None,
    channel28: BooleanInput = None,
    channel29: BooleanInput = None,
    channel30: BooleanInput = None,
    channel31: BooleanInput = None,
    channel32: BooleanInput = None,
    dynamic_channel: NumberInput = None,
) -> CompositeWire:
    """
    Outputs a composite signal that is the same as the input composite, but with one channel replaced by a boolean value.
    If channel is 0, will write to the channel specified by the dynamic channel input.
    """
    return Wire(
        SignalType.Composite,
        ComponentWrapper(
            CompositeWriteBoolean(
                0, Position(), 1 if dynamic_channel is None else 0, 32
            ),
            {
                "composite_signal_input": Wire.to(SignalType.Composite, composite),
                "start_channel_input": Wire.to(SignalType.Number, dynamic_channel),
                "channel_1_input": Wire.to(SignalType.Boolean, channel1),
                "channel_2_input": Wire.to(SignalType.Boolean, channel2),
                "channel_3_input": Wire.to(SignalType.Boolean, channel3),
                "channel_4_input": Wire.to(SignalType.Boolean, channel4),
                "channel_5_input": Wire.to(SignalType.Boolean, channel5),
                "channel_6_input": Wire.to(SignalType.Boolean, channel6),
                "channel_7_input": Wire.to(SignalType.Boolean, channel7),
                "channel_8_input": Wire.to(SignalType.Boolean, channel8),
                "channel_9_input": Wire.to(SignalType.Boolean, channel9),
                "channel_10_input": Wire.to(SignalType.Boolean, channel10),
                "channel_11_input": Wire.to(SignalType.Boolean, channel11),
                "channel_12_input": Wire.to(SignalType.Boolean, channel12),
                "channel_13_input": Wire.to(SignalType.Boolean, channel13),
                "channel_14_input": Wire.to(SignalType.Boolean, channel14),
                "channel_15_input": Wire.to(SignalType.Boolean, channel15),
                "channel_16_input": Wire.to(SignalType.Boolean, channel16),
                "channel_17_input": Wire.to(SignalType.Boolean, channel17),
                "channel_18_input": Wire.to(SignalType.Boolean, channel18),
                "channel_19_input": Wire.to(SignalType.Boolean, channel19),
                "channel_20_input": Wire.to(SignalType.Boolean, channel20),
                "channel_21_input": Wire.to(SignalType.Boolean, channel21),
                "channel_22_input": Wire.to(SignalType.Boolean, channel22),
                "channel_23_input": Wire.to(SignalType.Boolean, channel23),
                "channel_24_input": Wire.to(SignalType.Boolean, channel24),
                "channel_25_input": Wire.to(SignalType.Boolean, channel25),
                "channel_26_input": Wire.to(SignalType.Boolean, channel26),
                "channel_27_input": Wire.to(SignalType.Boolean, channel27),
                "channel_28_input": Wire.to(SignalType.Boolean, channel28),
                "channel_29_input": Wire.to(SignalType.Boolean, channel29),
                "channel_30_input": Wire.to(SignalType.Boolean, channel30),
                "channel_31_input": Wire.to(SignalType.Boolean, channel31),
                "channel_32_input": Wire.to(SignalType.Boolean, channel32),
            },
        ),
    )


def lua_script(
    script: str,
    composite_input: CompositeInput = None,
    video_input: VideoInput = None,
) -> tuple[CompositeWire, VideoWire]:
    """
    Executes a Lua script to process composite and video inputs and produce composite and video outputs.
    The script must define two functions: processComposite(input) and processVideo(input).
    """
    script_handling.verify_script(script)
    component = ComponentWrapper(
        LuaScript(0, Position(), script),
        {
            "data_input": Wire.to(SignalType.Composite, composite_input),
            "video_input": Wire.to(SignalType.Video, video_input),
        },
    )
    return Wire(SignalType.Composite, component), Wire(
        SignalType.Video, component, node_index=1
    )


def lua_script_file(
    file_path: str,
    composite_input: CompositeInput = None,
    video_input: VideoInput = None,
) -> tuple[CompositeWire, VideoWire]:
    """
    Takes a lua script from a file and embeds it. The file may use dependencies, which are automatically resolved.
    See lua_script for more information.
    """
    return lua_script(
        script_handling.resolve_and_verify_script(file_path),
        composite_input,
        video_input,
    )


def property_dropdown(
    options: dict[str, Number], default: str, name: str = "value"
) -> NumberWire:
    """
    A dropdown property that can be set in the microcontroller properties.
    Options should be a dictionary mapping option names to their corresponding numeric values.
    The default parameter should be the name of the option that is selected by default.
    """
    if default not in options:
        raise ValueError(f"Default value '{default}' not in options")
    dropdown_options = [DropDownOption(name, value) for name, value in options.items()]
    default_idx: int = list(options.keys()).index(default)
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            PropertyDropdown(0, Position(), default_idx, dropdown_options, name), {}
        ),
    )


def property_number(value: Number, name: str = "value") -> NumberWire:
    """
    A number property that can be set in the microcontroller properties.
    """
    return Wire(
        SignalType.Number,
        ComponentWrapper(PropertyNumber(0, Position(), name, value), {}),
    )


def property_slider(
    min_value: Number = 0,
    max_value: Number = 10,
    rounding: Number = 1,
    value: Number = 0,
    name: str = "value",
) -> NumberWire:
    """
    A slider property that can be set in the microcontroller properties.
    """
    if not min_value <= value <= max_value:
        raise ValueError("Value must be between min and max values")
    return Wire(
        SignalType.Number,
        ComponentWrapper(
            PropertySlider(0, Position(), min_value, max_value, value, rounding, name),
            {},
        ),
    )


def property_toggle(
    value: bool = False,
    name: str = "value",
    on_label: str = "on",
    off_label: str = "off",
) -> BooleanWire:
    """
    A toggle property that can be set in the microcontroller properties.
    """
    return Wire(
        SignalType.Boolean,
        ComponentWrapper(
            PropertyToggle(0, Position(), name, on_label, off_label, value), {}
        ),
    )
