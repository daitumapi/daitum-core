# Copyright 2026 Daitum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
The :class:`Reference` value type — a model-object reference that serialises to the
platform's ``!!!<id>`` form and decodes back to the live object via a load context.

A large share of the configuration package's custom ``build()`` overrides existed only
to emit ``f"!!!{obj.to_string()}"`` for a model :class:`~daitum_model.Parameter`,
:class:`~daitum_model.Calculation`, or field. ``Reference`` captures that single concept
symmetrically: it builds to the prefixed string and, given the original target's
``to_string()`` output, can be reconstructed during decoding. Storing a ``Reference`` as
a public attribute lets the default :class:`~daitum_model.serialisation.Buildable` walk
emit the reference key automatically, so those overrides collapse to the default walk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from daitum_model.serialisation import Buildable

if TYPE_CHECKING:
    from daitum_model.decoding import LoadContext

#: The platform prefix marking a string as a reference to a model object.
REFERENCE_PREFIX = "!!!"


@runtime_checkable
class Referable(Protocol):
    """Anything a :class:`Reference` can point at: it must render via ``to_string()``."""

    def to_string(self) -> str: ...


class Reference(Buildable):
    """A reference in ``!!!`` position, serialised as ``"!!!<target>"``.

    The target is usually a model object (:class:`~daitum_model.Parameter`,
    :class:`~daitum_model.Calculation`, or field), serialised via its ``to_string()``.
    A few sites (inequality bounds) also emit a plain numeric literal in the same
    ``!!!`` position; such a target is stored as the raw ``int``/``float`` and rendered
    directly. ``build()`` emits the prefixed form; :meth:`decode` is the inverse —
    a numeric body decodes to the number, an identifier body resolves through a
    :class:`~daitum_model.decoding.LoadContext` symbol table.
    """

    def __init__(self, target: Referable | int | float):
        self.target = target

    @property
    def id(self) -> str:
        """The bare (unprefixed, unbracketed) identifier of the target object."""
        return _bare_id(self._rendered_target())

    def _rendered_target(self) -> str:
        if isinstance(self.target, (int, float)):
            return str(self.target)
        return self.target.to_string()

    def build(self) -> str:  # type: ignore[override]
        """Serialise to the ``"!!!<target>"`` reference string."""
        return f"{REFERENCE_PREFIX}{self._rendered_target()}"

    @classmethod
    def decode(cls, value: str, ctx: LoadContext) -> Reference:
        """Reconstruct a :class:`Reference` from a ``"!!!<target>"`` string and a context.

        A numeric body is recovered as an ``int``/``float``; any other body is resolved
        to the live model object via ``ctx``.
        """
        if not is_reference(value):
            raise ValueError(f"Not a reference string: {value!r}")
        body = value.removeprefix(REFERENCE_PREFIX)
        number = _as_number(body)
        if number is not None:
            return cls(number)
        return cls(ctx.resolve(_bare_id(body)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Reference):
            return NotImplemented
        return self.build() == other.build()

    def __hash__(self) -> int:
        return hash(self.build())

    def __repr__(self) -> str:
        return f"Reference({self._rendered_target()!r})"


def is_reference(value: object) -> bool:
    """Return ``True`` if ``value`` is a ``"!!!..."`` reference string."""
    return isinstance(value, str) and value.startswith(REFERENCE_PREFIX)


def reference_number(value: str) -> int | float | None:
    """Return the numeric literal a reference encodes, or ``None`` if its body is an id.

    A few ``!!!`` positions (e.g. inequality-filter bounds) carry a plain number rather than
    a model-object id. This recovers that number so a decoder can tell the two apart without
    attempting symbol resolution.
    """
    if not is_reference(value):
        return None
    return _as_number(value.removeprefix(REFERENCE_PREFIX))


def _bare_id(rendered: str) -> str:
    """Strip a leading ``!!!`` and surrounding field brackets from a rendered reference.

    ``"!!!TOTAL_COST"`` -> ``"TOTAL_COST"``; ``"[Cost]"`` -> ``"Cost"``;
    ``"!!![Cost]"`` -> ``"Cost"``.
    """
    bare = rendered.removeprefix(REFERENCE_PREFIX)
    if bare.startswith("[") and bare.endswith("]"):
        bare = bare[1:-1]
    return bare


def _as_number(body: str) -> int | float | None:
    """Parse a reference body as an ``int``/``float`` literal, or ``None`` if it is an id.

    Mirrors how a numeric bound was stringified on the way out (``str(value)``), so the
    same text decodes back to the same number type.
    """
    try:
        return int(body)
    except ValueError:
        pass
    try:
        return float(body)
    except ValueError:
        return None
