"""
Adressable memory
"""

from typing import Literal

from sw_mc_builder import *
from sw_mc_builder.wire import Wire


def memory(
    rows: int,
    cols: int,
    input: Wire[Literal[SignalType.Composite]],
    write_pointer: Wire[Literal[SignalType.Number]],
    read_pointer: Wire[Literal[SignalType.Number]],
) -> tuple[Wire[Literal[SignalType.Composite]], Wire[Literal[SignalType.Composite]]]:
    regular_output = comp.unconnected(SignalType.Composite)
    last_output = comp.placeholder(SignalType.Composite)
    for row in range(1, rows + 1):
        write_selected = write_pointer == row
        read_selected = read_pointer == row
        output = comp.composite_write_number()
        for col in range(1, cols + 1):
            result = comp.memory_register(write_selected, data=input[col])
            switched = comp.numerical_switchbox(
                result, regular_output[col], read_selected
            )
            regular_output = regular_output.set(col, switched)
            output[col] = result
        last_output.replace_producer(output)
    return regular_output, last_output


read = comp.input(SignalType.Number, "Read Pointer")
write = comp.input(SignalType.Number, "Write Pointer")
val1 = comp.input(SignalType.Number, "Value 1")
val2 = comp.input(SignalType.Number, "Value 2")

in_wire = comp.composite_write_number(None, val1, val2)
reg, last = memory(7, 2, in_wire, write, read)

mc = Microcontroller("Memory controller", 3, 3)
mc.place_input(read, 0, 0)
mc.place_input(write, 0, 1)
mc.place_input(val1, 1, 0)
mc.place_input(val2, 1, 1)
mc.place_output(reg[1], "Regular 1", x=1, y=2)
mc.place_output(reg[2], "Regular 2", x=2, y=0)
mc.place_output(last[1], "Last 1", x=2, y=1)
mc.place_output(last[2], "Last 2", x=2, y=2)

if __name__ == "__main__":
    handle_mcs(mc)
