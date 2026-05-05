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

This module provides the Icon enum, which contains identifiers for all available
icons that can be used in UI components. Icons come from FontAwesome 6 and
custom Daitum application icon sets, organized by category and purpose.

Main Components
---------------

**Icon Enum:**
    Single enumeration containing all available icon identifiers organized into:

    - FontAwesome 6 solid icons (standard filled icons)
    - FontAwesome 6 regular icons (outlined variants)
    - Daitum validation icons
    - Daitum rostering & child care icons
    - Daitum model editor icons
    - Daitum common component icons
    - Special icons (NULL for empty/no icon)

Icon Categories
---------------

**FontAwesome 6 - Solid Icons:**
    Standard filled icons from FontAwesome 6, including:

    - Common UI icons (CIRCLE, STAR, LOCK, CLOCK)
    - Navigation icons (HOUSE, PLANE_UP, RIGHT_FROM_BRACKET)
    - Action icons (COPY, PEN_TO_SQUARE, PAPER_PLANE)
    - Domain-specific icons (BURGER, GAMING, ACCOMMODATION, WINE_BOTTLE)
    - Education icons (GRADUATION_CAP, BOOK, CHALKBOARD_USER)
    - Child care icons (HANDS_HOLDING_CHILD, CHILD_REACHING)
    - Activity icons (PERSON_SWIMMING, UMBRELLA_BEACH, TREE)
    - Finance icons (DOLLAR_SIGN, BRIEFCASE_MEDICAL)
    - Communication icons (COMMENT, CIRCLE_INFO)

**FontAwesome 6 - Regular Icons (Outlined):**
    Outlined variants of FontAwesome icons, prefixed with ``REG_``:

    - ``REG_STAR``, ``REG_BELL``, ``REG_CLOCK``
    - ``REG_CIRCLE``, ``REG_COMMENT``
    - ``REG_BURGER``, ``REG_GAMING``, ``REG_ACCOMMODATION``
    - Useful for lighter visual weight or inactive states

**Daitum Validation Icons:**
    - CHECK: Validation success indicator

**Daitum Rostering & Child Care Icons:**
    Specialized icons for rostering and child care applications:

    - Selection: SELECTED, UNSELECTED
    - Staff qualifications: QUALIFIED, CERT_ONLY, RESPONSIBLE_PERSON
    - Compliance: FIRST_AID, WWCC_VALID, WWCC_INVALID
    - Time management: CONTACT_TIME, BREAK_TIME, SHIFT_START_TYPE
    - Activities: PROGRAMMING, SWIMMING, STUDY, ISS
    - Operations: SHIFT_COVERAGE, ADJUST_ROSTER_ORDER, OPTIMISE
    - Actions: IMPORT, PUBLISH
    - Information: INFO, HELP, ALERT

**Daitum Model Editor Icons:**
    Array manipulation icons:

    - ADD_ROW: Add new row to array
    - REMOVE_ROW: Delete row from array
    - MOVE_ROW: Reorder rows in array

**Daitum Common Component Icons:**
    - RESET_ICON: Reset value to default

**Special Icons:**
    - NULL: Empty icon (renders nothing)

Icon Identifier Format
----------------------

Icon identifiers follow specific format patterns:

**FontAwesome Icons:**
    "FontAwesome.6.{ICON_NAME}"

    - Example: "FontAwesome.6.STAR"
    - Regular variants: "FontAwesome.6.REG_{ICON_NAME}"
    - Example: "FontAwesome.6.REG_STAR"

**Daitum Icons:**
    "Daitum.{category}.{subcategory}.{ICON_NAME}"

    - Validation: "Daitum.ribbonMenu.validationDialog.VALID"
    - Rostering: "Daitum.applications.rostering.forChildCare.{ICON_NAME}"
    - Editor: "Daitum.modelEditor.editors.array.{ICON_NAME}"
    - Components: "Daitum.commonComponents.{component}.{ICON_NAME}"

**Special:**
    - Empty string "" for NULL icon

Usage Patterns
--------------

Icons are typically used in two contexts:

1. **IconConfig for UI Elements:**
   Used with IconConfig to configure icon appearance with color

2. **Direct Icon References:**
   Used directly in component properties that accept icons

The Icon enum ensures type safety and provides autocomplete support
in development environments.

Examples
--------
Using icons with IconConfig::

    from daitum_ui.icons import Icon
    from daitum_ui.styles import IconConfig

    # Success icon in green
    success_icon = IconConfig(
        source=Icon.CHECK,
        color="#4caf50"
    )

    # Warning icon in orange
    warning_icon = IconConfig(
        source=Icon.TRIANGLE_EXCLAMATION,
        color="#ff9800"
    )

    # Star rating icon in gold
    star_icon = IconConfig(
        source=Icon.STAR,
        color="#ffd700"
    )

Using outlined icons for inactive states::

    # Active state - solid star
    active_icon = IconConfig(
        source=Icon.STAR,
        color="#ffc107"
    )

    # Inactive state - outlined star
    inactive_icon = IconConfig(
        source=Icon.REG_STAR,
        color="#9e9e9e"
    )

Using domain-specific icons::

    # Child care activity icons
    swimming_icon = IconConfig(source=Icon.SWIMMING, color="#2196f3")
    programming_icon = IconConfig(source=Icon.PROGRAMMING, color="#9c27b0")
    study_icon = IconConfig(source=Icon.STUDY, color="#ff5722")

    # Staff qualification icons
    qualified_icon = IconConfig(source=Icon.QUALIFIED, color="#4caf50")
    first_aid_icon = IconConfig(source=Icon.FIRST_AID, color="#f44336")

Using selection icons::

    # For icon checkbox states
    from daitum_ui.styles import IconCheckboxEditor

    checkbox_editor = IconCheckboxEditor(
        on_icon=IconConfig(source=Icon.SELECTED, color="#2196f3"),
        off_icon=IconConfig(source=Icon.UNSELECTED, color="#9e9e9e")
    )

Using action icons in buttons::

    from daitum_ui.elements import Button

    # Save button with paper plane icon
    save_button = Button(
        text_value="Send",
        icon_source=Icon.PAPER_PLANE.value,
        icon_color="#ffffff",
        background_color="#2196f3"
    )

    # Edit button with pen icon
    edit_button = Button(
        text_value="Edit",
        icon_source=Icon.PEN_TO_SQUARE.value,
        icon_color="#ffffff"
    )

Using compliance and validation icons::

    # WWCC validation status
    valid_wwcc = IconConfig(source=Icon.WWCC_VALID, color="#4caf50")
    invalid_wwcc = IconConfig(source=Icon.WWCC_INVALID, color="#f44336")

    # General validation check
    validation_check = IconConfig(source=Icon.CHECK, color="#4caf50")

Using information and help icons::

    # Information icon
    info_icon = IconConfig(
        source=Icon.INFO,
        color="#2196f3"
    )

    # Help icon
    help_icon = IconConfig(
        source=Icon.HELP,
        color="#9c27b0"
    )

    # Alert icon
    alert_icon = IconConfig(
        source=Icon.ALERT,
        color="#ff9800"
    )

Using NULL icon for conditional display::

    # Show icon only when condition is met
    conditional_icon = IconConfig(
        source=Icon.CHECK if is_valid else Icon.NULL,
        color="#4caf50"
    )

Using navigation icons::

    # Login/Logout
    login_icon = IconConfig(source=Icon.RIGHT_TO_BRACKET, color="#4caf50")
    logout_icon = IconConfig(source=Icon.RIGHT_FROM_BRACKET, color="#f44336")

    # Home navigation
    home_icon = IconConfig(source=Icon.HOUSE, color="#2196f3")

Using lock status icons::

    # Locked state
    locked_icon = IconConfig(source=Icon.LOCK, color="#f44336")

    # Unlocked state
    unlocked_icon = IconConfig(source=Icon.LOCK_OPEN, color="#4caf50")

Using array editor icons::

    # Row manipulation icons
    add_icon = IconConfig(source=Icon.ADD_ROW, color="#4caf50")
    remove_icon = IconConfig(source=Icon.REMOVE_ROW, color="#f44336")
    move_icon = IconConfig(source=Icon.MOVE_ROW, color="#2196f3")
"""

from enum import Enum


class Icon(Enum):
    """
    Enumeration of available icons for UI components.

    Icons are organized into several categories:

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

    # Daitum - Validation Icons
    CHECK = "Daitum.ribbonMenu.validationDialog.VALID"

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

    # Daitum - Model Editor Icons
    ADD_ROW = "Daitum.modelEditor.editors.array.ADD_ROW"
    REMOVE_ROW = "Daitum.modelEditor.editors.array.REMOVE_ROW"
    MOVE_ROW = "Daitum.modelEditor.editors.array.MOVE_ROW"

    # Daitum - Common Component Icons
    RESET_ICON = "Daitum.commonComponents.readOnlyResettableField.RESET_VALUE"

    # Daitum - Model Visualization
    CAMP = "Daitum.modelVisualisation.mapDisplay.CAMP"

    # Special - Empty/Null Icon
    NULL = ""
