from __future__ import annotations

from sw_mc_lib.Types import SignalType

import sw_mc_builder.components as comp
from sw_mc_builder import wire as wire_


def bool_to_int(
    value: wire_.BooleanWire, true_value: int = 1, false_value: int = 0
) -> wire_.NumberWire:
    return comp.numerical_switchbox(true_value, false_value, value)


def moving_avg(wire: wire_.NumberWire, count: int = 60) -> wire_.NumberWire:
    """
    Simple moving average over `count` ticks.
    :param wire: The input wire.
    :param count: Number of ticks to average over.
    :return: The averaged wire.
    """
    end = wire
    for _ in range(count):
        end = comp.function("x", end).stop_optimization()
    result = comp.placeholder(SignalType.Number)
    result.replace_producer(result + wire - end)
    return result / count
