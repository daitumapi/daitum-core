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
Toolbar configuration for standard table views.

This module provides the :class:`TableToolbar` class, which controls the toolbar shown above a
:class:`~daitum_ui.tabular.TableView`, and the :class:`Density` enum used for its default row
density.
"""

from enum import Enum

from typeguard import typechecked

from daitum_ui._buildable import Buildable


class Density(Enum):
    """
    Row density of a table. Each level has a fixed row height.

    Attributes:
        COMPACT: Shortest rows, fitting the most rows on screen.
        COMFORTABLE: Medium row height.
        SPACIOUS: Tallest rows.
    """

    COMPACT = "COMPACT"
    COMFORTABLE = "COMFORTABLE"
    SPACIOUS = "SPACIOUS"


@typechecked
class TableToolbar(Buildable):
    """
    Toolbar shown above a standard table view.

    Nothing is shown unless ``show_toolbar`` is set; each control can then be turned off on its
    own.

    Attributes:
        show_toolbar:
            Whether the toolbar is shown at all. When false every control below is hidden,
            whatever its own setting.
        show_search_bar:
            Search box filtering rows on the text of every column. The search term is not
            remembered between visits.
        show_filters:
            Button showing or hiding the per-column filter row. Only shown when the view's
            ``can_filter`` is also set.
        show_column_hiding:
            Menu for choosing which columns are shown. The user's choice is remembered per view.
        show_density_toggle:
            Toggle for switching the table's density. The user's choice is remembered per view.
        show_full_screen_toggle:
            Button showing the table full screen.
        default_density:
            Density used until the user picks one. A view's ``row_height``, when set, takes
            precedence and the density toggle is not shown.
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        show_toolbar: bool = False,
        show_search_bar: bool = True,
        show_filters: bool = True,
        show_column_hiding: bool = True,
        show_density_toggle: bool = True,
        show_full_screen_toggle: bool = True,
        default_density: Density = Density.COMFORTABLE,
    ) -> None:
        super().__init__()
        self.show_toolbar: bool = show_toolbar
        self.show_search_bar: bool = show_search_bar
        self.show_filters: bool = show_filters
        self.show_column_hiding: bool = show_column_hiding
        self.show_density_toggle: bool = show_density_toggle
        self.show_full_screen_toggle: bool = show_full_screen_toggle
        self.default_density: Density = default_density
