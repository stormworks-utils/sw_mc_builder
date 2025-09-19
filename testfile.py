from __future__ import annotations

from sw_mc_builder import *
from sw_mc_builder.microcontroller import Microcontroller

input_a = comp.input(SignalType.Number, "Input A")
input_b = comp.input(SignalType.Number, "Input B")

added = comp.add(input_a, input_b)
subbed = comp.sub(added, 5)

multiplied = comp.mul(subbed, added)

mc = Microcontroller("simple example")
mc.place_input(input_a, 0, 0)
mc.place_input(input_b, 1, 0)
mc.add_number_tooltip("Result", multiplied)
mc.place_output(multiplied, "Output", x=0, y=1)
print(mc._to_xml())
