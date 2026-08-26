from sw_mc_builder import *

input1 = comp.input(SignalType.Number, "Input 1")
input2 = comp.input(SignalType.Number, "Input 2")

composite = comp.composite_write_number(None, input1, input2)

composite = composite.set(1, composite[1] + composite[2])
composite = composite.set(2, input2)

mc = Microcontroller("Example MC")
mc.place_input(input1, 0, 0)
mc.place_input(input2, 0, 1)
mc.place_output(composite[1], "Added", x=1, y=0)

if __name__ == "__main__":
    handle_mcs(mc)
