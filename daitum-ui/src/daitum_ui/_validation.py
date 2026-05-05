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

from daitum_model.fields import ValidationFieldsContainer
from daitum_model.named_values import ValidationValuesContainer

from daitum_ui._colours import VALIDATION_BACKGROUND_COLOURS, VALIDATION_COLOURS
from daitum_ui.fixed_value_view import Cell
from daitum_ui.styles import ColumnStyle
from daitum_ui.tabular import ViewField


def _add_validation_formatting(
    view_value: ViewField | Cell,
    validation_value: ValidationFieldsContainer | ValidationValuesContainer,
    combined_message_value: str,
):
    """
    Apply severity-coloured conditional formatting to a ``ViewField`` or ``Cell``.

    Looks up the foreground and background colours for the validator's severity level and
    registers a conditional formatting rule on *view_value* using the corresponding
    ``__invalid__`` field or calculation as the trigger condition.

    Args:
        view_value: The UI field or cell to format.
        validation_value: The validation container holding the invalid field/value and severity.
        combined_message_value: The ID of the combined-message field/calculation to show as
            a tooltip.

    Returns:
        The updated *view_value* (for chaining).

    Raises:
        ValueError: If *view_value* and *validation_value* types are incompatible.
    """
    colour = VALIDATION_COLOURS.get(validation_value.severity)
    bg_colour = VALIDATION_BACKGROUND_COLOURS.get(validation_value.severity)

    if isinstance(view_value, ViewField) and isinstance(
        validation_value, ValidationFieldsContainer
    ):

        view_value.add_conditional_formatting_rule(
            validation_value.invalid_field.id,
            ColumnStyle(
                font_color=colour,
                background_color=bg_colour,
                tooltip_field=combined_message_value,
            ),
        )
    elif isinstance(view_value, Cell) and isinstance(validation_value, ValidationValuesContainer):
        view_value.add_conditional_formatting_rule(
            validation_value.invalid_value,
            ColumnStyle(
                font_color=colour,
                background_color=bg_colour,
                tooltip_field=combined_message_value,
            ),
        )
    else:
        raise ValueError("Invalid argument types")

    return view_value
