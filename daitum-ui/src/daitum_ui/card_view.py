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
Card-based view components for the UI Generator framework.

This module provides the CardView class, which enables displaying data in a
visually appealing card-style layout. Card views are ideal for presenting
structured information in a grid of individual cards, each representing a
single data record or item.

Classes:
    - CardView: View for displaying data in a card-based layout

Example:
    >>> # Define the data source
    >>> products_table = Table("products")
    >>>
    >>> # Create a card template
    >>> product_card = Card(
    ...     title_field=Field("product_name", DataType.STRING),
    ...     subtitle_field=Field("category", DataType.STRING),
    ...     image_field=Field("image_url", DataType.STRING),
    ...     description_field=Field("description", DataType.STRING)
    ... )
    >>>
    >>> # Create and register the card view
    >>> builder = UiBuilder()
    >>> card_view = builder.add_card_view(
    ...     card_template=product_card,
    ...     table=products_table,
    ...     display_name="Product Catalog"
    ... )
    >>>
"""

from daitum_model import Table
from typeguard import typechecked

from daitum_ui._buildable import json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.data import MatchRowFilterMode
from daitum_ui.elements import Card
from daitum_ui.filter_component import FilterableView, FilterComponent


@typechecked
@json_type_info("card")
class CardView(BaseView, FilterableView):
    """
    Represents a card-based view used to display data in a structured,
    card-style layout. A CardView defines which data source it draws from,
    how rows are filtered, and which card template is used to render each
    item.

    Attributes:
        card_template (Card):
            The card template used to render each row/item in the view.
        source_table (Optional[str]):
            The ID of the source table providing the data for the view.
        match_row_filter_mode (Optional[MatchRowFilterMode]):
            Controls how rows are included or excluded based on filtering rules.
    """

    def __init__(
        self,
        card_template: Card,
        display_name: str | None = None,
        hidden: bool = False,
    ):
        BaseView.__init__(self, hidden)
        if display_name is not None:
            self._display_name = display_name
        FilterableView.__init__(self, None)

        self.card_template = card_template
        self.source_table: str | None = None
        self.match_row_filter_mode: MatchRowFilterMode | None = None

    def set_table(self, table: Table) -> "CardView":
        """Sets the source data table for this card view."""
        self.source_table = table.id
        return self

    def set_match_row_filter_mode(self, match_row_filter_mode: MatchRowFilterMode) -> "CardView":
        """Sets the row filter mode controlling how rows are included or excluded."""
        self.match_row_filter_mode = match_row_filter_mode
        return self

    def set_use_filter(self, use_filter: FilterComponent) -> "CardView":
        """Attaches a filter component to this card view."""
        FilterableView.__init__(self, use_filter)
        return self
