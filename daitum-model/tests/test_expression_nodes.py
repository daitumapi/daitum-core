"""
Structural tests for the expression-node internals (Phase D — additive, post-refactor).

Unlike the behaviour corpus, these may legitimately inspect node classes directly: they verify the
new structured representation (children, node types, validation hooks) rather than the public
contract. They are additive and not part of the equivalence net.
"""

from __future__ import annotations

import pytest
from daitum_model import DataType, formulas
from daitum_model.expression import (
    ADD,
    BinaryOperator,
    ColumnAccess,
    ExpressionNode,
    Function,
    MemberAccess,
    UnaryOperator,
    ensure_operand,
)
from daitum_model.formula import CONST, Formula
from fixtures.contract_model import build_fixture


def _public_function_classes() -> list[type]:
    """Every concrete public formula-function node class (those with a ``name``)."""
    from daitum_model import _functions

    classes = [
        obj
        for obj in vars(_functions).values()
        if isinstance(obj, type)
        and issubclass(obj, Function)
        and obj is not Function
        and getattr(obj, "name", "")
    ]
    assert classes
    return classes


def _resolve_spec(cls: type) -> tuple:
    """Resolve a function class's ``spec``, whether a class tuple or an ``accepts``-derived property.

    The shape base classes (``_Reducer``/``_TypedUnary``) expose ``spec`` as a property reading
    ``self.accepts``; evaluate it against the class's ``accepts`` without constructing an instance.
    """
    from types import SimpleNamespace

    for klass in cls.__mro__:
        attr = klass.__dict__.get("spec")
        if isinstance(attr, property):
            return tuple(attr.fget(SimpleNamespace(accepts=getattr(cls, "accepts", None))))
        if isinstance(attr, tuple):
            return attr
    return ()


class TestConstant:
    def test_ensure_operand_wraps_literals(self):
        assert isinstance(ensure_operand(5), Formula)
        assert ensure_operand(5).to_data_type() == DataType.INTEGER

    def test_ensure_operand_passes_through_operands(self):
        fx = build_fixture()
        cost = fx.fields["Cost"]
        assert ensure_operand(cost) is cost


class TestOperatorNodes:
    def test_binary_operator_node_children(self):
        left, right = CONST(1), CONST(2)
        node = BinaryOperator(ADD, left, right, DataType.INTEGER)
        assert list(node.children()) == [left, right]
        assert node.to_string() == "(1 + 2)"
        assert node.to_data_type() == DataType.INTEGER

    def test_unary_negate_node(self):
        fx = build_fixture()
        node = UnaryOperator(fx.fields["Cost"], DataType.DECIMAL)
        assert list(node.children()) == [fx.fields["Cost"]]
        assert node.to_string() == "-([Cost])"

    def test_member_access_is_expression_node(self):
        fx = build_fixture()
        node = MemberAccess(fx.fields["Site"], "Amount")
        assert isinstance(node, ExpressionNode)
        assert len(node.children()) == 1
        assert node.to_string() == "[Site].[Amount]"

    def test_column_access_is_expression_node(self):
        fx = build_fixture()
        node = ColumnAccess(fx.table, "Cost")
        assert isinstance(node, ExpressionNode)
        assert node.children() == ()
        assert node.to_string() == "Jobs[Cost]"
        assert node.to_data_type() == DataType.DECIMAL_ARRAY


class TestFunctionNodes:
    def test_sum_node_children_and_type(self):
        from daitum_model._functions import Sum

        fx = build_fixture()
        cost, qty = fx.fields["Cost"], fx.fields["Qty"]
        node = Sum(cost, qty)
        assert list(node.children()) == [cost, qty]
        assert node.to_data_type() == DataType.DECIMAL
        assert node.to_string() == "SUM([Cost], [Qty])"

    def test_function_validate_hook_runs(self):
        from daitum_model._functions import Sum

        fx = build_fixture()
        with pytest.raises(ValueError):
            Sum(fx.fields["Name"])

    def test_lookup_array_renders_wire_name(self):
        from daitum_model._functions import LookupArray

        fx = build_fixture()
        node = LookupArray(fx.fields["Costs"], fx.fields["Costs"], fx.fields["Names"])
        # The Python name is LOOKUPARRAY but the wire name is LOOKUP_ARRAY.
        assert node.render_name() == "LOOKUP_ARRAY"
        assert node.to_string().startswith("LOOKUP_ARRAY(")

    def test_every_function_node_is_an_expression_node(self):
        for cls in _public_function_classes():
            assert issubclass(cls, ExpressionNode)

    def test_every_function_declares_an_argument_spec(self):
        """Coverage gate (Gap B): every function declares a named ``Arg`` spec — the single source
        of truth for validation and the generated per-argument docs. Only the genuinely
        zero-operand functions may carry an empty spec."""
        from daitum_model.expression import Arg

        zero_operand = {"BLANK", "ROWVECTOR"}
        for cls in _public_function_classes():
            # ``spec`` may be a class tuple or a property derived from ``accepts`` (the shape bases);
            # resolve it the way the engine does — off an instance is unsafe (needs args), so read
            # the class tuple or the property's result on the class via the MRO.
            spec = _resolve_spec(cls)
            assert all(isinstance(arg, Arg) for arg in spec), f"{cls.name}: spec must be Args"
            assert all(arg.name for arg in spec), f"{cls.name}: every Arg must be named"
            if cls.name in zero_operand:
                assert not spec, f"{cls.name}: expected an empty spec (zero operands)"
            else:
                assert spec, f"{cls.name}: must declare a non-empty argument spec"

    def test_no_argument_accepts_any(self):
        """Coverage gate: every declared argument lists its accepted types explicitly — no
        ``accepts=None`` (which the docs would render as ``ANY``). Relational positions still list
        the full concrete kind set (``ANY_TYPE``); they are never left unrestricted. This is what
        keeps the generated reference free of ``ANY``."""
        for cls in _public_function_classes():
            for arg in _resolve_spec(cls):
                assert arg.accepts is not None, (
                    f"{cls.name}.{arg.name}: accepts is None — declare its accepted types "
                    f"explicitly (use ANY_TYPE for genuinely unrestricted positions)"
                )


class TestTableIsOperand:
    def test_table_satisfies_operand_contract(self):
        from daitum_model.formula import Operand

        fx = build_fixture()
        assert isinstance(fx.table, Operand)
        assert fx.table.to_string() == "Jobs"
        assert fx.table.to_data_type().is_array()

    def test_table_used_as_operand_in_function(self):
        fx = build_fixture()
        # A bare table flows through ROWS as an object-array operand.
        assert formulas.ROWS(fx.table).to_string() == "ROWS(Jobs)"


class TestDependencies:
    """The structured-formula payoff: a formula knows the reference leaves it uses (§3.5)."""

    def test_function_collects_field_dependencies(self):
        fx = build_fixture()
        deps = formulas.SUM(fx.fields["Cost"], fx.fields["Qty"]).dependencies()
        assert deps == {fx.fields["Cost"], fx.fields["Qty"]}

    def test_nested_operators_collect_transitively(self):
        fx = build_fixture()
        expr = (fx.fields["Cost"] * fx.fields["Qty"]) + fx.fields["Cost"]
        # Identity-keyed: the repeated Cost leaf appears once.
        assert expr.dependencies() == {fx.fields["Cost"], fx.fields["Qty"]}

    def test_constant_has_no_dependencies(self):
        assert CONST(5).dependencies() == set()
        assert (CONST(1) + CONST(2)).dependencies() == set()

    def test_accumulator_loop_collects_each_term(self):
        fx = build_fixture()
        formula = CONST(0)
        for fid in ("Cost", "Qty"):
            formula += fx.fields[fid]
        assert formula.dependencies() == {fx.fields["Cost"], fx.fields["Qty"]}

    def test_calculation_and_parameter_are_leaves(self):
        fx = build_fixture()
        expr = fx.calc + fx.param
        assert expr.dependencies() == {fx.calc, fx.param}

    def test_member_access_collects_base_and_field(self):
        fx = build_fixture()
        deps = fx.fields["Site"]["Amount"].dependencies()
        # Both the base reference (Site) and the accessed field (Amount) are dependencies.
        assert fx.fields["Site"] in deps
        assert any(d.to_string() == "[Amount]" for d in deps)

    def test_column_access_depends_on_the_field(self):
        fx = build_fixture()
        deps = fx.table["Cost"].dependencies()
        assert any(d.to_string() == "[Cost]" for d in deps)

    def test_calculation_reports_its_own_formula_dependencies(self):
        # fx.calc is TotalCost = Cost * Qty — its direct dependencies are those two fields.
        fx = build_fixture()
        assert fx.calc.dependencies() == {fx.fields["Cost"], fx.fields["Qty"]}

    def test_calculated_field_reports_its_formula_dependencies(self):
        fx = build_fixture()
        field = fx.table.add_calculated_field(
            "Total", formulas.SUM(fx.fields["Cost"], fx.fields["Qty"])
        )
        assert field.dependencies() == {fx.fields["Cost"], fx.fields["Qty"]}

    def test_combo_field_reports_its_formula_dependencies(self):
        fx = build_fixture()
        field = fx.table.add_combo_field(
            "Combo", fx.fields["Cost"] * fx.fields["Qty"], calculate_in_optimiser=True
        )
        assert field.dependencies() == {fx.fields["Cost"], fx.fields["Qty"]}

    def test_constant_field_has_empty_dependencies(self):
        # A calculated field whose formula is a literal constant references nothing.
        fx = build_fixture()
        field = fx.table.add_calculated_field("Const", CONST(2.0))
        assert field.dependencies() == set()
