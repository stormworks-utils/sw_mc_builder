from sw_mc_lib.Components import ArithmeticFunction8In
from sw_mc_lib.Types import SignalType

import sw_mc_builder.components as comp
from sw_mc_builder.component_wrapper import ComponentWrapper
from sw_mc_builder.optimizer import optimize_arithmetic
from sw_mc_builder.pseudo_components import PseudoComponent


class TestOptimizer:
    def test_self_referential_counter_is_not_inlined_into_self_referential_function(
        self,
    ) -> None:
        counter = comp.placeholder(SignalType.Number)
        is_zero = counter > 0
        counter.replace_producer(is_zero.int())
        feedback = counter + is_zero.int()

        optimize_arithmetic([feedback])

        counter_producer = counter.producer
        feedback_producer = feedback.producer
        assert isinstance(counter_producer, ComponentWrapper)
        assert isinstance(feedback_producer, ComponentWrapper)
        assert isinstance(counter_producer.inner_component, ArithmeticFunction8In)
        assert isinstance(feedback_producer.inner_component, ArithmeticFunction8In)
        assert counter_producer is not feedback_producer
        assert counter_producer.inputs["x_input"].producer is counter_producer
        assert isinstance(counter_producer.inputs["y_input"].producer, PseudoComponent)
        assert feedback_producer.inputs["x_input"].producer is counter_producer
        assert isinstance(feedback_producer.inputs["y_input"].producer, PseudoComponent)
        assert counter_producer.inner_component.function == "(((1-sgn(0-x))/2))*(1)+((1-((1-sgn(0-x))/2)))*(0)"
        assert feedback_producer.inner_component.function == "x+((((1-sgn(0-x))/2))*(1)+((1-((1-sgn(0-x))/2)))*(0))"
