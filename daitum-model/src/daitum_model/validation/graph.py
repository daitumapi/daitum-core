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
A normalised, read-only view of a :class:`~daitum_model.ModelBuilder` for validation rules.

:class:`ModelGraph` is built once per validation pass. It provides symbol tables (ids to
live objects) and dependency adjacency so each rule can query the model without re-walking
raw builder objects. Rules must compare references by ``.id`` against these symbol tables —
never by object equality — because operands define no value ``__eq__`` / ``__hash__`` (the
``dependencies()`` set is identity-keyed; see :meth:`daitum_model.formula.Formula.dependencies`).
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from daitum_model.data_types import MapDataType, ObjectDataType
from daitum_model.derived_table import DerivedTable
from daitum_model.fields import CalculatedField, ComboField, Field
from daitum_model.joined_table import JoinedTable
from daitum_model.named_values import Calculation
from daitum_model.tables import Table
from daitum_model.union_table import UnionTable

if TYPE_CHECKING:
    from daitum_model.formula import Operand
    from daitum_model.model import ModelBuilder
    from daitum_model.named_values import Parameter


def detect_cycles(edges: dict[str, set[str]]) -> list[list[str]]:
    """Return the groups of nodes that participate in a dependency cycle.

    Uses Kahn's algorithm (the same approach as the decode-path
    :func:`daitum_model._decoders.tables.dependency_order`), but is *non-raising*: after
    repeatedly removing nodes with no outstanding dependencies, whatever remains is exactly
    the set of nodes on (or feeding into) a cycle. Those remaining nodes are returned as
    connected groups so a rule can report each cycle separately.

    Args:
        edges: A node id mapped to the set of node ids it depends on. Edges to unknown
            nodes and self-edges are ignored (a self-edge is not treated as a cycle here,
            matching the decoder).

    Returns:
        A list of cyclic node groups (each sorted); empty when the graph is acyclic.
    """
    known = set(edges)
    pending = {node: (deps & known) - {node} for node, deps in edges.items()}

    changed = True
    while changed:
        changed = False
        ready = [node for node, deps in pending.items() if not deps]
        for node in ready:
            del pending[node]
            changed = True
        if ready:
            ready_set = set(ready)
            for deps in pending.values():
                deps.difference_update(ready_set)

    if not pending:
        return []
    return _connected_groups(pending)


def find_cycle_path(edges: dict[str, set[str]], nodes: list[str]) -> list[str]:
    """Return one concrete cycle within ``nodes`` as an ordered path ``[a, b, ..., a]``.

    ``nodes`` is a group returned by :func:`detect_cycles` (every node reaches a cycle). A
    depth-first walk restricted to that group is guaranteed to close a loop; the returned
    path starts and ends on the same node so it renders as ``a -> b -> a``. Falls back to
    the sorted group (unclosed) only if no closable loop is found, which cannot happen for a
    genuine :func:`detect_cycles` group but keeps the function total.
    """
    scope = set(nodes)
    # Exclude self-edges, matching detect_cycles: a table referencing itself is not a cycle.
    adjacency = {node: sorted((edges.get(node, set()) & scope) - {node}) for node in nodes}

    for origin in sorted(nodes):
        path = _dfs_to_origin(origin, adjacency)
        if path is not None:
            return path

    return sorted(nodes)


def _dfs_to_origin(origin: str, adjacency: dict[str, list[str]]) -> list[str] | None:
    """Depth-first search for a path from ``origin`` back to ``origin`` (a closed cycle)."""
    stack: list[str] = [origin]
    on_path = {origin}
    # (node, index-of-next-neighbour-to-try) frames make this an explicit iterative DFS.
    frames: list[list] = [[origin, 0]]
    while frames:
        node, index = frames[-1]
        neighbours = adjacency[node]
        if index >= len(neighbours):
            frames.pop()
            popped = stack.pop()
            on_path.discard(popped)
            continue
        frames[-1][1] += 1
        nxt = neighbours[index]
        if nxt == origin:
            return stack + [origin]
        if nxt not in on_path:
            stack.append(nxt)
            on_path.add(nxt)
            frames.append([nxt, 0])
    return None


def _connected_groups(pending: dict[str, set[str]]) -> list[list[str]]:
    """Partition the leftover (cyclic) nodes into weakly-connected groups."""
    adjacency: dict[str, set[str]] = {node: set() for node in pending}
    for node, deps in pending.items():
        for dep in deps:
            if dep in adjacency:
                adjacency[node].add(dep)
                adjacency[dep].add(node)

    groups: list[list[str]] = []
    unseen = set(pending)
    while unseen:
        start = next(iter(unseen))
        group: set[str] = set()
        queue = deque([start])
        while queue:
            current = queue.popleft()
            if current in group:
                continue
            group.add(current)
            unseen.discard(current)
            queue.extend(neighbour for neighbour in adjacency[current] if neighbour not in group)
        groups.append(sorted(group))

    return sorted(groups)


class ModelGraph:
    """Normalised view of a model's tables, fields, named values, and dependencies."""

    def __init__(
        self,
        tables: dict[str, Table],
        fields_by_table: dict[str, dict[str, Field]],
        named_values: dict[str, Calculation | Parameter],
        table_edges: dict[str, set[str]],
        named_value_edges: dict[str, set[str]],
    ) -> None:
        self.tables = tables
        self.fields_by_table = fields_by_table
        self.named_values = named_values
        self.table_edges = table_edges
        self.named_value_edges = named_value_edges

    @classmethod
    def from_model(cls, model: ModelBuilder) -> ModelGraph:
        """Build the normalised graph from an assembled :class:`ModelBuilder`."""
        tables: dict[str, Table] = {table.id: table for table in model.get_tables()}
        fields_by_table: dict[str, dict[str, Field]] = {
            table.id: dict(table.field_definitions) for table in model.get_tables()
        }

        named_values: dict[str, Calculation | Parameter] = {}
        # pylint: disable=protected-access
        for parameter in model._parameters:
            named_values[parameter.id] = parameter
        for calculation in model._calculations:
            named_values[calculation.id] = calculation

        table_edges = cls._build_table_edges(model)
        named_value_edges = cls._build_named_value_edges(model)

        return cls(tables, fields_by_table, named_values, table_edges, named_value_edges)

    @staticmethod
    def _build_table_edges(model: ModelBuilder) -> dict[str, set[str]]:
        """Table id to the ids of tables it must be built after.

        Edges come from three sources: structural sources (derived/join/union), object/map
        reference fields, and *formula* references — a calculated/combo field whose formula
        reads a field or table belonging to another table creates a build-order edge too.
        Including formula edges is what lets a cycle like "B derived from A, and a calculated
        field on A looks up into B" be detected.
        """
        edges: dict[str, set[str]] = {}
        for table in model.get_tables():
            deps: set[str] = set()

            if isinstance(table, DerivedTable):
                deps.add(table.source_table_id)
            elif isinstance(table, JoinedTable):
                for condition in table.join_conditions:
                    deps.add(condition.left_table_id)
                    deps.add(condition.right_table_id)
            elif isinstance(table, UnionTable):
                deps.update(source.source_table_id for source in table.source_tables)

            for field in table.field_definitions.values():
                data_type = field.data_type
                if isinstance(data_type, (ObjectDataType, MapDataType)):
                    deps.add(data_type.table_id)
                if isinstance(field, (CalculatedField, ComboField)):
                    deps.update(ModelGraph._referenced_table_ids(field.dependencies()))

            edges[table.id] = deps
        return edges

    @staticmethod
    def _referenced_table_ids(leaves: set[Operand]) -> set[str]:
        """The ids of tables a set of formula reference leaves reads from.

        A ``Field`` leaf contributes its owning table; a ``Table`` leaf contributes itself.
        ``Calculation`` / ``Parameter`` leaves are model-level and contribute no table edge.
        """
        table_ids: set[str] = set()
        for leaf in leaves:
            if isinstance(leaf, Field):
                table_ids.add(leaf.table.id)
            elif isinstance(leaf, Table):
                table_ids.add(leaf.id)
        return table_ids

    @staticmethod
    def _build_named_value_edges(model: ModelBuilder) -> dict[str, set[str]]:
        """Calculation id to the ids of named values its formula transitively references."""
        # pylint: disable=protected-access
        edges: dict[str, set[str]] = {}
        for parameter in model._parameters:
            edges[parameter.id] = set()
        for calculation in model._calculations:
            deps: set[str] = set()
            for leaf in calculation.dependencies():
                leaf_id = getattr(leaf, "id", None)
                if isinstance(leaf, Calculation) and leaf_id is not None:
                    deps.add(leaf_id)
            edges[calculation.id] = deps
        return edges

    def intra_table_field_edges(self, table_id: str) -> dict[str, set[str]]:
        """Field-to-field dependency edges *within* one table.

        Maps each calculated/combo field id on ``table_id`` to the ids of fields **on the
        same table** its formula depends on. Cross-table dependencies are deliberately
        excluded — those are covered by the table-level cycle rule — so this graph only
        exposes cycles internal to a single table.
        """
        fields = self.fields_by_table.get(table_id, {})
        edges: dict[str, set[str]] = {}
        for field_id, field in fields.items():
            if isinstance(field, (CalculatedField, ComboField)):
                deps = {
                    leaf.id
                    for leaf in field.dependencies()
                    if isinstance(leaf, Field) and leaf.table.id == table_id and leaf.id in fields
                }
                edges[field_id] = deps
        return edges

    def has_field(self, table_id: str, field_id: str) -> bool:
        """Whether ``field_id`` exists on the table ``table_id`` in this model."""
        return field_id in self.fields_by_table.get(table_id, {})

    def resolve_field(self, table_id: str, field_id: str) -> Field | None:
        """Return the field ``field_id`` on ``table_id``, or ``None`` if absent."""
        return self.fields_by_table.get(table_id, {}).get(field_id)

    def available_fields(self, table_id: str) -> list[str]:
        """Sorted field ids on ``table_id`` (empty if the table is unknown)."""
        return sorted(self.fields_by_table.get(table_id, {}))

    @staticmethod
    def formula_dependencies(obj: CalculatedField | ComboField | Calculation) -> set[Operand]:
        """The identity-keyed reference leaves an object's formula uses.

        A thin wrapper over the existing ``dependencies()`` primitive, kept here so rules
        have a single, well-named entry point.
        """
        return obj.dependencies()
