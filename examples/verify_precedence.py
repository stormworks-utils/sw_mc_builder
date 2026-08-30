from sw_mc_builder import *


OPS = ["+", "-", "*", "/", "%", "^"]

result = comp.constant_on()
for op1, op2 in ((a, b) for a in OPS for b in OPS):
    equation = f"12{op1}3{op2}7"
    if op1 == op2 == "^":
        # other result would be too big
        equation = "2^3^0.5"
    python_result = eval(equation.replace("^", "**"))
    result = result & comp.equal(comp.function(equation), python_result, 0.001)

mc = Microcontroller("Operator Precedence Test Suite", width=1, length=1)
mc.add_boolean_tooltip("Result", result)

if __name__ == "__main__":
    handle_mcs(mc)
