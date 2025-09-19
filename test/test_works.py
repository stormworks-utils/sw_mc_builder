import unittest

from sw_mc_lib import Position
from sw_mc_lib.Components import ConstantOn
from sw_mc_lib.Types import SignalType

from sw_mc_builder.component_wrapper import ComponentWrapper
from sw_mc_builder.wire import Wire


class Test(unittest.TestCase):
    def test_placeholder(self) -> None:
        Wire(SignalType.Video, ComponentWrapper(ConstantOn(1, Position()), {}))
