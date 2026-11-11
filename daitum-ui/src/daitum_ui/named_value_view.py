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
Named value view components for the UI Generator framework.

Named value views pair each label with a value and display them in either a
horizontal or vertical layout, suited to summaries, dashboards, and information
panels.

Example:
    >>> builder = UiBuilder()
    >>> summary_view = builder.add_named_value_view(
    ...     display_name="Sales Summary",
    ...     orientation=Orientation.HORIZONTAL
    ... )
    >>> summary_view.add_value(
    ...     ViewField(total_sales, display_name="Total Sales")
    ... )
    >>> summary_view.add_value(
    ...     ViewField(order_count, display_name="Orders")
    ... )
"""

from enum import Enum

from typeguard import typechecked

from daitum_ui._buildable import json_type_info
from daitum_ui.base_view import BaseView
from daitum_ui.tabular import ViewField


class Orientation(Enum):
    """
    Specifies the layout orientation for views.

    Attributes:
        HORIZONTAL: Horizontal layout orientation
        VERTICAL: Vertical layout orientation
    """

    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"


@typechecked
@json_type_info("named values")
class NamedValueView(BaseView):
    """
    A view that displays named values in a specified orientation.

    Named value views present key-value pairs or labelled data elements,
    organised either horizontally or vertically based on the orientation setting.

    Attributes:
        orientation (Orientation):
            The layout orientation for displaying values.
            Defaults to HORIZONTAL.
        values (list):
            List of value definitions to be displayed in the view.
    """

    def __init__(
        self,
        display_name: str | None = None,
        hidden: bool = False,
        orientation: Orientation = Orientation.HORIZONTAL,
    ):
        """
        Initializes a NamedValueView with optional display settings.

        Args:
            display_name (Optional[str]):
                Optional name for display.
            hidden (bool):
                If True, the view is not visible in the UI. Defaults to False.
            orientation (Orientation):
                The layout orientation. Defaults to HORIZONTAL.
        """
        super().__init__(hidden)
        if display_name is not None:
            self._display_name = display_name
        self.show_band_color: bool = True
        self.show_dropdowns_below: bool = True
        self.orientation = orientation
        self.values: list[ViewField] = []

    def add_value(self, view_field: ViewField):
        self.values.append(view_field)
