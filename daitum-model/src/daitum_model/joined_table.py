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
``JoinedTable`` and its supporting ``JoinType`` enum and ``JoinCondition`` value object.

A joined table is the cross-product of two or more source tables filtered by one or more
``JoinCondition`` rows. The ``JoinType`` chosen on each condition controls how unmatched rows
on either side are handled.
"""

from __future__ import annotations

from enum import Enum

from typeguard import typechecked

from daitum_model.serialisation import Buildable

from .fields import Field
from .tables import Table


class JoinType(Enum):
    """The type of join used by a :class:`JoinCondition` to combine rows from two tables."""

    LEFT = "LEFT"
    """
    Keep every row from the left table; attach matching right-table values where they exist,
    and leave the right-side cells blank otherwise.

    Example — joining ``Orders`` (3 rows) to ``Customers`` (2 rows) on
    ``Orders.customer_id == Customers.id``::

        Orders               Customers
        order_id  cust_id    cust_id  name
        --------  -------    -------  -----
        1         A          A        Alice
        2         B          C        Carol
        3         D

        LEFT result (3 rows -- one per Orders row):
        order_id  cust_id  name
        --------  -------  -------
        1         A        Alice
        2         B        <blank>
        3         D        <blank>
    """

    RIGHT = "RIGHT"
    """
    Keep every row from the right table; attach matching left-table values where they exist,
    and leave the left-side cells blank otherwise. Mirror image of :attr:`LEFT`.

    Same source tables as the LEFT example::

        RIGHT result (2 rows -- one per Customers row):
        order_id  cust_id  name
        --------  -------  -----
        1         A        Alice
        <blank>   C        Carol
    """

    INNER = "INNER"
    """
    Keep only rows where the join condition matches on both sides. Unmatched rows from either
    table are dropped.

    Same source tables as the LEFT example::

        INNER result (1 row -- only A matches on both sides):
        order_id  cust_id  name
        --------  -------  -----
        1         A        Alice
    """

    FULL = "FULL"
    """
    Keep every row from both tables. Where a row has no match on the other side, the missing
    cells are blank. Equivalent to a :attr:`LEFT` join unioned with a :attr:`RIGHT` join.

    Same source tables as the LEFT example::

        FULL result (4 rows -- 3 from Orders + 1 unmatched Customer):
        order_id  cust_id  name
        --------  -------  -------
        1         A        Alice
        2         B        <blank>
        3         D        <blank>
        <blank>   C        Carol
    """

    CROSS = "CROSS"
    """
    Pair every row from the left table with every row from the right table (the Cartesian
    product). A ``CROSS`` join has no match fields: pass neither ``left_field`` nor
    ``right_field`` to the :class:`JoinCondition` (supplying either raises ``ValueError``).

    Same source tables as the LEFT example::

        CROSS result (6 rows -- 3 Orders x 2 Customers):
        order_id  cust_id  name
        --------  -------  -----
        1         A        Alice
        1         A        Carol
        2         B        Alice
        2         B        Carol
        3         D        Alice
        3         D        Carol
    """


@typechecked
class JoinCondition(Buildable):
    """
    Represents a condition for joining two tables.

    For matching joins (:attr:`JoinType.LEFT`, :attr:`JoinType.RIGHT`,
    :attr:`JoinType.INNER`, :attr:`JoinType.FULL`) both ``left_field`` and ``right_field``
    must be supplied — they are the fields matched between the two tables. A
    :attr:`JoinType.CROSS` join pairs every left row with every right row and takes no match
    fields: ``left_field`` and ``right_field`` must both be omitted.
    """

    def __init__(
        self,
        left_table: Table,
        right_table: Table,
        join_type: JoinType,
        left_field: Field | None = None,
        right_field: Field | None = None,
    ):
        if join_type is JoinType.CROSS:
            if left_field is not None or right_field is not None:
                raise ValueError(
                    "A CROSS join pairs every row from both tables and takes no match fields; "
                    "do not provide left_field or right_field."
                )
        elif left_field is None or right_field is None:
            raise ValueError(
                f"A {join_type.value} join requires both left_field and right_field to match "
                f"rows between the two tables."
            )

        self._left_table = left_table
        self._left_field = left_field
        self._right_table = right_table
        self._right_field = right_field

        self.left_table_id = left_table.id
        self.left_table_field = left_field.id if left_field is not None else None
        self.right_table_id = right_table.id
        self.right_table_field = right_field.id if right_field is not None else None
        self.join_type = join_type

    @property
    def left_table(self) -> Table:
        return self._left_table

    @property
    def left_field(self) -> Field | None:
        return self._left_field

    @property
    def right_table(self) -> Table:
        return self._right_table

    @property
    def right_field(self) -> Field | None:
        return self._right_field


@typechecked
class JoinedTable(Table):
    """
    Represents a table resulting from a join operation.

    A `JoinedTable` is a table that is constructed by joining two or more other tables based on
    specific join conditions. A join operation combines rows from different tables based on a
    related field (column) between them. The `join_conditions` list defines how these tables are
    connected and which fields from the tables are used for the join.

    Joins can be of different types, such as `INNER`, `LEFT`, `RIGHT`, `FULL`, and `CROSS`, and they
    dictate how the rows from the tables are combined and which rows are included in the final
    result.

    A `JoinCondition` consists of the following:
        - `left_table`: The left table involved in the join.
        - `right_table`: The right table involved in the join.
        - `join_type`: The type of join (e.g., INNER, LEFT, RIGHT, FULL, CROSS).
        - `left_field`: The field in the left table that is used to match with the right table.
          Omitted for a `CROSS` join.
        - `right_field`: The field in the right table that is used to match with the left table.
          Omitted for a `CROSS` join.

    A `CROSS` join takes no match fields and pairs every left row with every right row.

    Multiple `JoinCondition` objects can be specified to represent more complex join scenarios. Each
    condition defines how a pair of tables are joined, and having multiple conditions allows for
    joining more than two tables at once, with each pair of tables joined based on the specific
    conditions defined. When there are multiple `JoinCondition` objects, the joins are performed in
    sequence, and the resulting table combines the results of all the joins.
    """

    def __init__(
        self,
        id: str,
        join_conditions: list[JoinCondition],
    ):
        super().__init__(id)
        self.join_conditions = join_conditions

    def add_table_reference(self, source_table: Table) -> Field:
        """
        Adds a reference to a table in the `JoinedTable`.

        This method allows for adding a reference field for a source table that is part of the join
        conditions. If the source table is not part of the join conditions, a `ValueError` will be
        raised.

        Args:
            source_table (Table): The table to be referenced.

        Returns:
            Field: The reference field for the source table.

        Raises:
            ValueError: If the source table is not present in any of the join conditions.
        """
        all_tables = list(
            {jc.left_table for jc in self.join_conditions}
            | {jc.right_table for jc in self.join_conditions}
        )

        if source_table not in all_tables:
            raise ValueError(
                f"The provided source table with id {source_table.id} is not present in the "
                f"JoinedTable"
            )

        table_object_reference = self.add_object_reference_field(source_table.id, source_table)

        return table_object_reference
