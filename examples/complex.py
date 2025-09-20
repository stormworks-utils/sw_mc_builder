from sw_mc_builder import *

input1 = comp.input(SignalType.Number, "Input 1")

result = util.moving_avg(input1, 100000)

mc = Microcontroller("Example MC")
mc.place_input(input1, 0, 0)
mc.place_output(result, "Moving Average", x=1, y=0)

handle_mcs(mc)