from sw_mc_builder import *

process_variable = comp.input(SignalType.Number, "Process variable")
setpoint = comp.input(SignalType.Number, "Setpoint")

P = 0.5
I = 0.0005
D = 1
MIN_I = -1
MAX_I = 1

diff = setpoint - process_variable

procedural = diff * P
integral = comp.placeholder(SignalType.Number)
integral.replace_producer((integral + diff * I).clamp(MIN_I, MAX_I))
derivative = (
    comp.function("x", process_variable).stop_optimization() - process_variable
) * D

result = procedural + integral + derivative

mc = Microcontroller("Simple PID")
mc.place_input(process_variable, 0, 0)
mc.place_input(setpoint, 0, 1)
mc.place_output(result, "PID Value", x=1, y=0)

if __name__ == "__main__":
    handle_mcs(mc)
