from sw_mc_builder import *

starter = comp.input(SignalType.Boolean, "Starter")
engine_data = comp.input(SignalType.Composite, "Engine Data")
engine_rps = comp.input(SignalType.Number, "Engine RPS")
throttle = comp.input(SignalType.Number, "Throttle")

target_rps = comp.property_slider(5, 20, 1, 10, "Target RPS")

idling = throttle == 0
actual_rps_target = comp.numerical_switchbox(4, target_rps, idling)

engine_air, engine_fuel, engine_temp = engine_data[:3]
afr = engine_air / engine_fuel
actual_starter = starter & (engine_temp < 100)
engine_slow = engine_rps < 3

clutch_enable = ~engine_slow & actual_starter
engine_rps_delayed = comp.function("x", engine_rps).stop_optimization()

rps_avg = (engine_rps + engine_rps_delayed) / 2

engine_integral = comp.placeholder(SignalType.Number)
engine_integral.replace_producer(
    (engine_integral + (actual_rps_target - rps_avg) * 0.005).clamp(0.01, 1)
)


clutch = comp.placeholder(SignalType.Number)
clutch.replace_producer(
    (clutch + (actual_rps_target * 0.85 - rps_avg) * -0.004).clamp(0, throttle**0.5)
    * clutch_enable.int()
)

engine_procedural = (actual_rps_target - rps_avg) * 0.05
engine_derivative = (engine_rps_delayed - engine_rps) * 0
engine_pid = (engine_integral + engine_derivative + engine_procedural).clamp(0, 1)

engine_throttle = engine_pid * actual_starter.int()

fuel_multi = comp.placeholder(SignalType.Number)
target_afr = afr - 13.3 - engine_temp / 100
binary_throttle = (engine_throttle * 1000).clamp(0, 0.001)
fuel_multi.replace_producer(
    (fuel_multi + target_afr * binary_throttle).clamp(0.4, 0.95)
)

engine_fuel = engine_throttle * fuel_multi

mc = Microcontroller("Engine Controller", 3, 3, "Constant RPS engine controller")
mc.place_input(starter, 0, 2)
mc.place_input(engine_data, 2, 1)
mc.place_input(engine_rps, 1, 1)
mc.place_input(throttle, 2, 2)
mc.place_output(engine_temp > 35, "Cooling Fans", x=0, y=0)
mc.place_output(actual_starter & engine_slow, "Starter Motor", x=0, y=1)
mc.place_output(clutch, "Clutch", x=1, y=0)
mc.place_output(engine_throttle, "Engine air", x=2, y=0)
mc.place_output(engine_fuel, "Engine fuel", x=1, y=2)
mc.add_number_tooltip("RPS", engine_rps)
mc.add_number_tooltip("Target RPS", actual_rps_target)
mc.add_number_tooltip("Clutch", clutch)
mc.add_number_tooltip("Engine Throttle", engine_throttle)
mc.add_number_tooltip("Engine Fuel multi", fuel_multi)
mc.add_number_tooltip("AFR", afr)
mc.add_number_tooltip("Engine Integral", engine_integral)

if __name__ == "__main__":
    handle_mcs(mc)
