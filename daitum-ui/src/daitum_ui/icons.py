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
Icon enumeration for UI components.

Provides the Icon enum of identifiers for every icon usable in UI components.
Icons are drawn from FontAwesome 6 (solid and regular variants) and custom
Daitum application icon sets. Icons are typically passed to ``IconConfig`` to
set appearance and colour, or referenced directly by component properties.

Examples:
    Using an icon with ``IconConfig``::

        from daitum_ui.icons import Icon
        from daitum_ui.styles import IconConfig

        success_icon = IconConfig(source=Icon.CHECK, color="#4caf50")
"""

from enum import Enum


class Icon(Enum):
    """
    Enumeration of available icons for UI components.

    Icons are organised into several categories:

    **FontAwesome 6 Icons:**
        - Standard icons (solid variants)
        - Regular (outlined) variants prefixed with ``REG_``

    **Daitum Application Icons:**
        - Rostering and child care specific icons
        - Model editor icons
        - Common component icons

    Each enum value contains the full icon identifier string used by the
    rendering system to locate and display the appropriate icon.
    """

    # FontAwesome 6 - Solid Icons
    BEER_MUG_EMPTY = "FontAwesome.6.BEER_MUG_EMPTY"
    ACCOMMODATION = "FontAwesome.6.ACCOMMODATION"
    BOTTLE_SHOP = "FontAwesome.6.BOTTLE_SHOP"
    CIRCLE = "FontAwesome.6.CIRCLE"
    BURGER = "FontAwesome.6.BURGER"
    GAMING = "FontAwesome.6.GAMING"
    PEN_TO_SQUARE = "FontAwesome.6.PEN_TO_SQUARE"
    TRIANGLE_EXCLAMATION = "FontAwesome.6.TRIANGLE_EXCLAMATION"
    STAR = "FontAwesome.6.STAR"
    USER_PEN = "FontAwesome.6.USER_PEN"
    PLANE_UP = "FontAwesome.6.PLANE_UP"
    COPY = "FontAwesome.6.COPY"
    LOCK = "FontAwesome.6.LOCK"
    LOCK_OPEN = "FontAwesome.6.LOCK_OPEN"
    CLOCK = "FontAwesome.6.CLOCK"
    PERSON_SWIMMING = "FontAwesome.6.PERSON_SWIMMING"
    BOOK_OPEN_READER = "FontAwesome.6.BOOK_OPEN_READER"
    RIGHT_FROM_BRACKET = "FontAwesome.6.RIGHT_FROM_BRACKET"
    RIGHT_TO_BRACKET = "FontAwesome.6.RIGHT_TO_BRACKET"
    CHALKBOARD_USER = "FontAwesome.6.CHALKBOARD_USER"
    DOLLAR_SIGN = "FontAwesome.6.DOLLAR_SIGN"
    BRIEFCASE_MEDICAL = "FontAwesome.6.BRIEFCASE_MEDICAL"
    AWARD = "FontAwesome.6.AWARD"
    GRADUATION_CAP = "FontAwesome.6.GRADUATION_CAP"
    HANDS_HOLDING_CHILD = "FontAwesome.6.HANDS_HOLDING_CHILD"
    TREE = "FontAwesome.6.TREE"
    UMBRELLA_BEACH = "FontAwesome.6.UMBRELLA_BEACH"
    ADDRESS_BOOK = "FontAwesome.6.ADDRESS_BOOK"
    CALENDAR_X_MARK = "FontAwesome.6.CALENDAR_X_MARK"
    CHILD_REACHING = "FontAwesome.6.CHILD_REACHING"
    BOLT = "FontAwesome.6.BOLT"
    PAPER_PLANE = "FontAwesome.6.PAPER_PLANE"
    CIRCLE_INFO = "FontAwesome.6.CIRCLE_INFO"
    BOOK = "FontAwesome.6.BOOK"
    COMMENT = "FontAwesome.6.COMMENT"
    WINE_BOTTLE = "FontAwesome.6.WINE_BOTTLE"
    HOUSE = "FontAwesome.6.HOUSE"
    DICE = "FontAwesome.6.DICE"
    HALF_CIRCLE = "FontAwesome.6.HALF_CIRCLE"
    TRUCK = "FontAwesome.6.TRUCK"
    CIRCLE_CHECK = "FontAwesome.6.CIRCLE_CHECK"
    TRASH_CAN = "FontAwesome.6.TRASH_CAN"
    CIRCLE_MINUS = "FontAwesome.6.CIRCLE_MINUS"
    PLUS = "FontAwesome.6.PLUS"
    XMARK = "FontAwesome.6.XMARK"
    GRIP_LINES = "FontAwesome.6.GRIP_LINES"
    ROTATE_LEFT = "FontAwesome.6.ROTATE_LEFT"
    EMPTY_FILTER = "FontAwesome.6.EMPTY_FILTER"
    FILLED_FILTER = "FontAwesome.6.FILLED_FILTER"
    REMOVE_FILTER = "FontAwesome.6.REMOVE_FILTER"
    EMPTY_FILTERS = "FontAwesome.6.EMPTY_FILTERS"
    FILLED_FILTERS = "FontAwesome.6.FILLED_FILTERS"

    # FontAwesome Pro - Solid Icons
    LOCATION_DOT = "FAPro.solid.LOCATION_DOT"
    LOCATION_PIN = "FAPro.solid.LOCATION_PIN"
    MAP_MARKER_PLUS = "FAPro.solid.MAP_MARKER_PLUS"
    MAP_MARKER_CHECK = "FAPro.solid.MAP_MARKER_CHECK"
    HELMET_SAFETY = "FAPro.solid.HELMET_SAFETY"
    USER_HELMET_SAFETY = "FAPro.solid.USER_HELMET_SAFETY"
    PERSON_DIGGING = "FAPro.solid.PERSON_DIGGING"

    # FontAwesome 6 - Regular (Outlined) Icons
    REG_STAR = "FontAwesome.6.REG_STAR"
    REG_BELL = "FontAwesome.6.REG_BELL"
    REG_CLOCK = "FontAwesome.6.REG_CLOCK"
    REG_CIRCLE_QUESTION = "FontAwesome.6.REG_CIRCLE_QUESTION"
    REG_COMMENT = "FontAwesome.6.REG_COMMENT"
    REG_DICE = "FontAwesome.6.REG_DICE"
    REG_BURGER = "FontAwesome.6.REG_BURGER"
    REG_GAMING = "FontAwesome.6.REG_GAMING"
    REG_BOTTLE_SHOP = "FontAwesome.6.REG_BOTTLE_SHOP"
    REG_CIRCLE = "FontAwesome.6.REG_CIRCLE"
    REG_HALF_CIRCLE = "FontAwesome.6.REG_HALF_CIRCLE"
    REG_ACCOMMODATION = "FontAwesome.6.REG_ACCOMMODATION"

    # Daitum - Rostering & Child Care Application Icons
    CONTACT_TIME = "Daitum.applications.rostering.forChildCare.CONTACT_TIME"
    SELECTED = "Daitum.applications.rostering.forChildCare.SELECTED"
    UNSELECTED = "Daitum.applications.rostering.forChildCare.UNSELECTED"
    RESPONSIBLE_PERSON = "Daitum.applications.rostering.forChildCare.RESPONSIBLE_PERSON"
    QUALIFIED = "Daitum.applications.rostering.forChildCare.QUALIFIED"
    CERT_ONLY = "Daitum.applications.rostering.forChildCare.CERT_ONLY"
    ADJUST_ROSTER_ORDER = "Daitum.applications.rostering.forChildCare.ADJUST_ROSTER_ORDER"
    FIRST_AID = "Daitum.applications.rostering.forChildCare.FIRST_AID"
    WWCC_VALID = "Daitum.applications.rostering.forChildCare.WWCC_VALID"
    WWCC_INVALID = "Daitum.applications.rostering.forChildCare.WWCC_INVALID"
    SHIFT_START_TYPE = "Daitum.applications.rostering.forChildCare.SHIFT_START_TYPE"
    BREAK_TIME = "Daitum.applications.rostering.forChildCare.BREAK_TIME"
    IMPORT = "Daitum.applications.rostering.forChildCare.IMPORT"
    PROGRAMMING = "Daitum.applications.rostering.forChildCare.PROGRAMMING"
    SWIMMING = "Daitum.applications.rostering.forChildCare.SWIMMING"
    STUDY = "Daitum.applications.rostering.forChildCare.STUDY"
    ISS = "Daitum.applications.rostering.forChildCare.ISS"
    SHIFT_COVERAGE = "Daitum.applications.rostering.forChildCare.SHIFT_COVERAGE"
    OPTIMISE = "Daitum.applications.rostering.forChildCare.OPTIMISE"
    PUBLISH = "Daitum.applications.rostering.forChildCare.PUBLISH"
    INFO = "Daitum.applications.rostering.forChildCare.INFO"
    HELP = "Daitum.applications.rostering.forChildCare.HELP"
    ALERT = "Daitum.applications.rostering.forChildCare.ALERT"

    ADD_ROW = "FontAwesome.6.PLUS"  # Deprecated: use PLUS
    REMOVE_ROW = "FontAwesome.6.XMARK"  # Deprecated: use XMARK
    MOVE_ROW = "FontAwesome.6.GRIP_LINES"  # Deprecated: use GRIP_LINES
    CHECK = "FontAwesome.6.CIRCLE_CHECK"  # Deprecated: use CIRCLE_CHECK
    RESET_ICON = "FontAwesome.6.ROTATE_LEFT"  # Deprecated: use ROTATE_LEFT

    # TODO - update once FontAwesome versions available
    CAMP = "Daitum.modelVisualisation.mapDisplay.CAMP"
    RESTORE_ORIGINAL = "Daitum.commonComponents.readOnlyResettableField.RESTORE_ORIGINAL"

    # Special - Empty/Null Icon
    NULL = ""
