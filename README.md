# Stormworks Microcontroller framework

A framework for building microcontrollers in Stormworks: Build and Rescue using python scripts.

## Features

- Modular design: Easily create and manage multiple microcontroller scripts.
- Latency optimization: Arithmetic functions are collapsed into function blocks in order to reduce latency.
- Auto layout: Automatically arrange function blocks for better readability.
- Integration with `tumfl` for lua verification and minification.
- Implicit constant number creation.

## Example

```python
from sw_mc_builder import *

input1 = comp.input(SignalType.Number, "Input 1")
input2 = comp.input(SignalType.Number, "Input 2")

added = input1 + input2 * 2
highest = input1.max(input2)

mc = Microcontroller("Example MC")
mc.place_input(input1, 0, 0)
mc.place_input(input2, 0, 1)
mc.place_output(added, "Added", x=1, y=0)
mc.place_output(highest, "Highest", x=1, y=1)
```

## Design

There are two predominant design patterns used in this framework:

### Python operators

```python
from sw_mc_builder import *

input1 = comp.input(SignalType.Number, "Input 1")
input2 = comp.input(SignalType.Number, "Input 2")

added = input1 + input2
maxed = (added * input2).max(1)
```

Each operation is represented as a python expression. This makes it very easy to write and read code,
but latency is harder to reason about, as some operations can result in multiple components.
> [!WARNING]
> There are some operands which are impossible to implement as python expressions, see below.

### Component functions

```python
from sw_mc_builder import *

input1 = comp.input(SignalType.Number, "Input 1")
input2 = comp.input(SignalType.Number, "Input 2")

added = comp.add(input1, input2)
multiplied = comp.mul(added, input2)
maxed = comp.function("max(x,y)", multiplied, 1)
```

Each function represents exactly one component. This makes latency very easy to reason about, as each function has a
fixed latency of one tick.

> [!WARNING]
> The optimizer might collapse multiple arithmetic operations into a single function block, which can affect latency.

> [!INFO]
> It is discouraged to use numerical or boolean function blocks. In part due to the poor readability,
> but also because some parts of the optimizer work better, if there are no function blocks.

### Caveats of using python operators

 - `and`: Use `&` instead. Keep in mind that `&` has a different operator precedence than `and`.
 - `or`: Use `|` instead. Keep in mind that `|` has a different operator precedence than `or`.
 - `not`: Use `~` instead. Keep in mind that `~` has a different operator precedence than `not`.
 - `int`: Use `<Wire>.int()` instead. Will convert a boolean to a number (0 or 1).
 - `__getindex__`: (`<Wire>[index]`): will always return a number. If you want to get a boolean, use
   `<Wire>.get_bool(index)` instead.
 - `__setindex__`: (`<Wire>[index] = value`): This will create a new composite write for each write.

### Functions other than python operators

The `Wire` class has a few functions that are possible with function blocks.

- `max(other)`: Maximum of two wires.
- `min(other)`: Minimum of two wires.
- `clamp(min, max)`: Clamp the wire between min and max.
- `lerp(start, end)`: Linear interpolation between two wires.
- `sin()`: Sine of the wire (in radians).
- `cos()`: Cosine of the wire (in radians).
- `tan()`: Tangent of the wire (in radians).
- `asin()`: Arcsine of the wire (in radians).
- `acos()`: Arccosine of the wire (in radians).
- `atan()`: Arctangent of the wire (in radians).
- `atan2(other)`: Arctangent of the wire and another wire (in radians).
- `sqrt()`: Square root of the wire.
- `ceil()`: Ceiling of the wire.
- `floor()`: Floor of the wire.
- `round(ndigits)`: Round the wire.
- `sgn()`: Sign of the wire.
- `switch(on_wire, off_wire)`: Switch between two wires based on the boolean value of the wire.

### Optimizer

All arithmetic operations are collapsed into a single function block in order to reduce latency.
This can be disabled per node or per mc.

```python
from sw_mc_builder import *

input1 = comp.input(SignalType.Number, "Input 1")

# Delay signal by one tick, disabling optimization for this node
delayed = comp.function("x", input1).stop_optimization()

# Disable optimization for the entire microcontroller
mc = Microcontroller("name")
mc.stop_optimization()
```
