"""
Decoder coverage gate (LOADABLE_PLAN.md §8.3).

Enumerates every concrete ``Buildable`` subclass across the three packages and asserts each
is either decodable (a registered decoder, or a registered ``@type`` variant) or carries an
explicit, documented exemption. A newly-added Buildable therefore fails CI until it is either
given a decoder or deliberately exempted here — gaps stay visible.

This is a *membership* gate: necessary but not sufficient. That a class has a registered
decode path does not prove the decoder works. Correctness (same type, byte-identical rebuild)
is proven by the per-class round-trip tests and, exhaustively for the template-based UI
classes, by ``test_every_representative_decodes_faithfully`` in ``test_ui_decoders.py``.

Exemptions fall into two kinds:
  * INLINE — the type is never decoded standalone; its parent's hand decoder reconstructs it
    (e.g. a nested specification, or a leaf reconstructed inside the owning object's decoder).
  * UNIMPLEMENTED — a real gap: this type is not yet on the decode path. Listed so coverage is
    honest and the remaining work is enumerated, not hidden.
"""

import importlib
import inspect
import pkgutil

import daitum_configuration
import daitum_ui

import daitum_model
from daitum_model.decoding import DECODER_REGISTRY, TYPE_REGISTRY
from daitum_model.serialisation import Buildable

# Types decoded inline by a parent decoder — correct to omit from the top-level registry.
_INLINE = {
    # Model: reconstructed inside their owning table/field/model decoders.
    "Field",
    "DataField",
    "CalculatedField",
    "ComboField",
    "ObjectDataType",
    "MapDataType",
    "JoinCondition",
    "UnionSource",
    "Reference",
    # Tracking groups and baselines are reconstructed inline by the top-level model decoder
    # (decode_model) via add_tracking_group / add_baseline.
    "TrackingGroup",
    "Baseline",
    # Configuration: nested objects rebuilt by their parent's hand decoder.
    "ConstraintSpecification",
    "DVSpecification",
}

# Real gaps — not yet decodable. The configuration decoder is now complete; if a future
# Buildable is added without a decoder it must be implemented or listed here with a reason.
_UNIMPLEMENTED: set[str] = set()


def _concrete_buildables(pkg) -> set[type]:
    found: set[type] = set()
    for _, name, _ in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        try:
            module = importlib.import_module(name)
        except Exception:  # noqa: BLE001 - skip modules that fail to import in isolation
            continue
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(obj, Buildable)
                and obj is not Buildable
                and obj.__module__.startswith(pkg.__name__)
                and not getattr(obj, "__abstractmethods__", None)
            ):
                found.add(obj)
    return found


def _register_all_packages() -> None:
    """Idempotently register every package's decoders so the registries are fully populated."""
    import daitum_configuration._decoders
    import daitum_ui._decoders

    import daitum_model._decoders

    daitum_model._decoders.register_all()
    daitum_configuration._decoders.register_all()
    daitum_ui._decoders.register_all()


def _registered() -> set[type]:
    """Every class reachable by a real decode path (not a replay shortcut)."""
    covered = set(DECODER_REGISTRY) | {c for m in TYPE_REGISTRY.values() for c in m.values()}
    # The UI package also decodes via its leaf registry and template factories.
    from daitum_ui._decoders._template import TEMPLATE_FACTORIES
    from daitum_ui._decoders.leaves import LEAF_DECODERS

    return covered | set(LEAF_DECODERS) | set(TEMPLATE_FACTORIES)


def _undecodable(pkg, exempt: set[str]) -> set[str]:
    _register_all_packages()
    registered = _registered()
    # Every concrete ``Formula`` node (``Constant`` and the per-function / operator node classes)
    # serialises to ``{dataType, formulaString}`` and decodes through the single ``Formula``
    # decoder, which dispatches on the declared ``Formula`` field type and parses the string back
    # into the specific subclass — so a subclass is covered transitively whenever ``Formula`` is
    # registered. They need no per-class decoder.
    from daitum_model.formula import Formula

    formula_decoded = Formula in registered
    names = {
        b.__name__
        for b in _concrete_buildables(pkg)
        if b not in registered and not (formula_decoded and issubclass(b, Formula))
    }
    return names - _INLINE - exempt


class TestDecoderCoverage:
    def test_model_package_fully_covered(self):
        # The model package decodes its entire public surface (no unimplemented gaps).
        assert _undecodable(daitum_model, set()) == set()

    def test_configuration_has_no_unexpected_gaps(self):
        # Every config Buildable is registered, decoded inline, or a documented gap.
        assert _undecodable(daitum_configuration, _UNIMPLEMENTED) == set()

    def test_ui_package_fully_covered(self):
        # Every concrete UI Buildable is decodable via a registered/leaf/template decoder.
        assert _undecodable(daitum_ui, set()) == set()

    def test_every_view_type_is_decodable(self):
        # Every concrete BaseView subclass must have a registered @type decode path, so a new
        # view added without a decoder fails CI rather than silently failing to load.
        from daitum_ui._decoders import register_all
        from daitum_ui.base_view import BaseView

        register_all()
        view_variants = set(TYPE_REGISTRY.get(BaseView, {}).values())
        undecodable = {
            cls.__name__
            for cls in _concrete_subclasses(BaseView)
            if cls not in view_variants and cls.__name__ not in _VIEW_INLINE
        }
        assert undecodable == set()

    def test_exemptions_are_disjoint(self):
        assert _INLINE.isdisjoint(_UNIMPLEMENTED)

    def test_inline_exemptions_are_still_concrete_buildables(self):
        # Guard against rot: an INLINE name that no longer matches any concrete Buildable is a
        # stale exemption (a renamed/removed class) silently weakening the gate.
        all_names = {
            b.__name__
            for pkg in (daitum_model, daitum_configuration, daitum_ui)
            for b in _concrete_buildables(pkg)
        }
        stale = _INLINE - all_names
        assert stale == set(), f"INLINE entries matching no concrete Buildable: {stale}"


#: Concrete BaseView subclasses decoded by a parent path, not their own @type.
#: GridView/FlexView share the "composite" discriminator with CompositeView (resolved by the
#: parentStyles ``display`` value), so they are decodable but not keyed in the BaseView registry.
_VIEW_INLINE = {"GridView", "FlexView"}


def _concrete_subclasses(base: type) -> set[type]:
    found: set[type] = set()
    stack = list(base.__subclasses__())
    while stack:
        cls = stack.pop()
        stack.extend(cls.__subclasses__())
        if not getattr(cls, "__abstractmethods__", None) and getattr(cls, "_type_name", None):
            found.add(cls)
    return found
