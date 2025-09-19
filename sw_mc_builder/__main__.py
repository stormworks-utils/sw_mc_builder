import sys
import runpy
from argparse import ArgumentParser
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sw_mc_builder._handling_arguments import parser_arguments

BLANK_MC: str = """\
from sw_mc_builder import *

input1 = comp.input(SignalType.Number, "Input 1")
input2 = comp.input(SignalType.Number, "Input 2")

added = input1 + input2

mc = Microcontroller("Example MC")
mc.place_input(input1, 0, 0)
mc.place_input(input2, 0, 1)
mc.place_output(added, "Added", x=1, y=0)

handle_mcs(mc)
"""


@contextmanager
def temporary_argv(new_argv: list[str]) -> Generator[None, None, None]:
    old = sys.argv
    sys.argv = list(new_argv)
    try:
        yield
    finally:
        sys.argv = old

def execute_child_script(child_path: Path, args: list[str]) -> None:
    resolved_child_path = str(child_path.resolve())
    # argv[0] will be the script filename (often useful to child)
    argv: list[str] = [resolved_child_path, *args]
    with temporary_argv(argv):
        # run as if executed directly: __name__ == "__main__"
        runpy.run_path(resolved_child_path, run_name="__main__")

def initialize_mc(name: Path) -> None:
    name = name.with_suffix(".py")
    if name.exists():
        print(f"Error: File {name} already exists.")
        sys.exit(1)
    with name.open("w") as file:
        file.write(BLANK_MC)
    print(f"Initialized new microcontroller project at {name}")


def main() -> None:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    init = subparsers.add_parser("init", help="Initialize a new microcontroller project")
    init.add_argument("name", type=Path, help="Name of the microcontroller project")
    init.set_defaults(func="init")
    execute = subparsers.add_parser("execute", help="Execute a microcontroller project")
    execute.add_argument("name", type=Path, help="Path to the microcontroller definition file")
    parser_arguments(execute)
    execute.set_defaults(func="execute")
    args = parser.parse_args()
    if args.func == "init":
        initialize_mc(args.name)
    elif args.func == "execute":
        execute_child_script(args.name, sys.argv[2:])


if __name__ == "__main__":
    main()
