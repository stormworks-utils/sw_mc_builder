from sw_mc_builder import *

first_wire = comp.input(SignalType.Composite, "First Composite")
second_wire = comp.input(SignalType.Composite, "Second Composite")

result = comp.unconnected(SignalType.Composite)
result[:4] = first_wire[:4]
result[5:8] = second_wire[:4]

mc = Microcontroller("Composite Write Example")
mc.place_input(first_wire, 0, 0)
mc.place_input(second_wire, 0, 1)
mc.place_output(result, "Result", x=1, y=0)

if __name__ == "__main__":
    handle_mcs(mc)
