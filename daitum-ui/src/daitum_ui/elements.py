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
UI element definitions for the UI Generator system.

The building blocks for constructing user interfaces: base classes, layout
containers, and interactive/display/input elements. Elements support state
management, data binding, and event handling, and compose into views. The
classes and enums below document their own options.

Example::

    # Static text, and dynamic text bound to a field
    label = Text(value="Hello World", font_weight=FontWeight.BOLD)
    user_name = Text(value=user_table.name_field, color="#333333")
"""

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, cast

from daitum_model import (
    Baseline,
    Calculation,
    DataType,
    Field,
    ObjectDataType,
    Parameter,
    Severity,
    Table,
)
from daitum_model.named_values import NamedValue
from typeguard import typechecked

from daitum_ui._buildable import Buildable, json_type_info
from daitum_ui._data import (
    DataValidationRule,
    DefaultValueReference,
    ModelPermissionsCondition,
    ModelVariable,
    ModelVariableCondition,
    ModelVariableType,
)
from daitum_ui.context_variable import ContextVariable
from daitum_ui.data import (
    Condition,
    ConstantCondition,
    DataValidationType,
    DecimalValue,
    DefaultValueBehaviour,
    DefaultValueType,
    IntegerValue,
    StringValue,
    ValidationFlag,
    Value,
)
from daitum_ui.icons import Icon
from daitum_ui.model_event import ModelEvent
from daitum_ui.styles import HorizontalAlignment, IconConfig
from daitum_ui.template_binding_key import TemplateBindingKey

from ._link_destination import ModelEditorLinkDestination

#: What an input element may bind to. A ``Field``/``Parameter``/``Calculation``/``ContextVariable``
#: is resolved and (where typed) validated; an already-resolved ``ModelVariable`` is passed through
#: verbatim (used by form adders for context-variable references and by the decoder).
DataSource = Field | Parameter | Calculation | ContextVariable | ModelVariable


class ElementSize(Enum):
    """
    Represents predefined size options for UI elements.
    """

    EXTRA_SMALL = "EXTRA_SMALL"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    EXTRA_LARGE = "EXTRA_LARGE"
    TWO_EXTRA_LARGE = "TWO_EXTRA_LARGE"
    THREE_EXTRA_LARGE = "THREE_EXTRA_LARGE"
    FIT_WIDTH = "FIT_WIDTH"


class TextVariant(Enum):
    """
    Defines how text should be semantically or visually presented.

    Attributes:
        SPAN:
            Inline text (e.g., for labels or short phrases).
        PARAGRAPH:
            Block-level text intended to occupy its own paragraph.
    """

    SPAN = "SPAN"
    PARAGRAPH = "PARAGRAPH"


class FontWeight(Enum):
    """
    Represents the thickness or boldness of the text.

    Attributes:
        REGULAR:
            Standard body-weight text.
        SEMI_BOLD:
            A slightly heavier weight, often used for emphasis.
        BOLD:
            Strong emphasis or headings.
    """

    REGULAR = "REGULAR"
    SEMI_BOLD = "SEMI_BOLD"
    BOLD = "BOLD"


class BadgeVariant(Enum):
    """
    The display variant of the badge.

    Attributes:
        DEFAULT:
            Standard visual appearance.
        UPDATED:
            Indicates a visually updated or emphasised state.
    """

    DEFAULT = "DEFAULT"
    UPDATED = "UPDATED"


class ContainerType(Enum):
    """
    The layout type for arranging child elements within a container.

    Options:
        FLEX:
            Uses a flexible box layout model for responsive design.
        GRID:
            Uses a grid layout model for structured arrangement.
    """

    FLEX = "flex"
    GRID = "grid"


class LayoutStyle(Enum):
    """
    Defines the layout style used when rendering elements inside the card.
    """

    LIST = "LIST"
    GRID = "GRID"


class GridOrder(Enum):
    """
    Defines how elements are arranged in GRID layout mode.

    ROW:
        Every second element is placed in the second column.
    COLUMN:
        The first column is filled up to `row_count` items before placing
        additional items in the second column.
    """

    ROW = "ROW"
    COLUMN = "COLUMN"


class RowSpacing(Enum):
    """
    Controls vertical spacing between elements within the card.
    """

    NONE = "NONE"
    TIGHT = "TIGHT"
    RELAXED = "RELAXED"


class AlignContent(Enum):
    """
    Controls how elements are aligned within the card’s container.
    """

    CENTER = "CENTER"
    SPACE_BETWEEN = "SPACE_BETWEEN"


class LayoutDirection(Enum):
    """
    Defines the direction in which items are laid out.

    ROW:
        Items are laid out horizontally.
    COLUMN:
        Items are laid out vertically.
    """

    ROW = "ROW"
    COLUMN = "COLUMN"


class OverflowStrategy(Enum):
    """
    Defines how content that exceeds its container bounds should be handled.

    Attributes:
        CLIP: Truncates (clips) the overflowing content so that only the visible
              portion within the container is shown.
        SCROLL: Enables scrolling, allowing users to access overflowing content
                via scroll interaction.
        SUMMARISE: Condenses or summarises the overflowing content into a shorter
                   representation (e.g., "..." or aggregated view).
    """

    CLIP = "CLIP"
    SCROLL = "SCROLL"
    SUMMARISE = "SUMMARISE"


class DateTimeMode(Enum):
    """
    The portion of a date/time value a :class:`DateTimePicker` edits.

    Attributes:
        DATE: Edits a calendar date only.
        TIME: Edits a time of day only.
        DATE_TIME: Edits a combined date and time.
    """

    DATE = "DATE"
    TIME = "TIME"
    DATE_TIME = "DATE_TIME"


class TextInputResize(Enum):
    """
    Controls how a multiline :class:`TextInput` may be resized by the user.

    Attributes:
        NONE: Not resizable.
        BOTH: Resizable horizontally and vertically.
        HORIZONTAL: Resizable horizontally only.
        VERTICAL: Resizable vertically only.
    """

    NONE = "NONE"
    BOTH = "BOTH"
    HORIZONTAL = "HORIZONTAL"
    VERTICAL = "VERTICAL"


class IconSet(Enum):
    """
    Catalogue of icons exposed by :class:`IconPicker`.

    Values match the platform ``IconPicker.IconSet`` enum.
    """

    ALL = "ALL"
    DAITUM = "DAITUM"
    FONT_AWESOME = "FONT_AWESOME"
    FA_PRO = "FA_PRO"


class ArrayLayout(Enum):
    """
    How an :class:`ArrayElement` lays out its values.

    Attributes:
        BADGE: One badge per value, with a "+N" badge for the values that do not fit.
        LIST: The values comma-separated on one line.
        COLUMN: One fixed-width slot per value.
    """

    BADGE = "BADGE"
    LIST = "LIST"
    COLUMN = "COLUMN"


class Shadow(Enum):
    """
    Drop shadow applied to a :class:`Card`.

    Attributes:
        NONE: No shadow.
        EXTRA_SMALL: Extra-small shadow.
        SMALL: Small shadow.
        MEDIUM: Medium shadow.
    """

    NONE = "NONE"
    EXTRA_SMALL = "EXTRA_SMALL"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"


@dataclass
@typechecked
class ElementStates(Buildable):
    """Holds the conditional state flags for a UI element. Each flag is a list of
    :class:`~daitum_ui.data.Condition` instances; the element enters that state when
    any condition evaluates to true."""

    is_disabled: list[Condition] | None = None
    is_required: list[Condition] | None = None
    is_read_only: list[Condition] | None = None
    is_error: list[Condition] | None = None
    is_warning: list[Condition] | None = None
    is_success: list[Condition] | None = None
    is_hidden: list[Condition] | None = None
    is_info: list[Condition] | None = None
    reserve_space: list[Condition] | None = None


@typechecked
def get_boolean_variable(variable: Field | Parameter | Calculation | bool):
    """
    Converts a boolean-like input into a ModelVariable representing a boolean
    value within the model.

    Parameters:
        variable (Field | Parameter | Calculation | bool):
            The source of the boolean value. Must resolve to DataType.BOOLEAN
            when a Field, Parameter, or Calculation is provided.

    Returns:
        ModelVariable:
            A model variable referencing the appropriate underlying boolean source.

    Raises:
        ValueError:
            If the provided Field, Parameter, or Calculation does not represent
            a boolean data type.
    """
    if isinstance(variable, Field):
        if variable.data_type != DataType.BOOLEAN:
            raise ValueError(
                f"Field {variable.id} is not a boolean field, cannot convert to ModelVariable."
            )
        return ModelVariable(ModelVariableType.FIELD, variable.id)

    if isinstance(variable, Parameter | Calculation):
        if variable.to_data_type() != DataType.BOOLEAN:
            raise ValueError(
                f"Named value {variable.id} is not a boolean field, cannot convert to "
                f"ModelVariable."
            )
        return ModelVariable(ModelVariableType.NAMED_VALUE, variable.id)

    return ModelVariable(ModelVariableType.CONTEXT_VARIABLE, "TRUE" if variable else "FALSE")


@typechecked
def get_boolean_condition(variable: Field | Parameter | Calculation | bool) -> Condition:
    """
    Convert a boolean-like input into a :class:`Condition`.

    A raw ``bool`` becomes a :class:`ConstantCondition`; a boolean ``Field``, ``Parameter``,
    or ``Calculation`` becomes a :class:`ModelVariableCondition` referencing that variable.

    Parameters:
        variable (Field | Parameter | Calculation | bool):
            The source of the boolean value. Must resolve to ``DataType.BOOLEAN`` when a
            ``Field``, ``Parameter``, or ``Calculation`` is provided.

    Raises:
        ValueError:
            If the provided ``Field``, ``Parameter``, or ``Calculation`` does not represent
            a boolean data type.
    """
    if isinstance(variable, bool):
        return ConstantCondition(value=variable)
    return ModelVariableCondition(model_variable=get_boolean_variable(variable))


@typechecked
class BaseElement(ABC, Buildable):
    """
    Base class for all UI elements that support state management.

    This class provides helper methods for configuring an element's
    interactive properties.

    Attributes:
        element_states (Optional[ElementStates]):
            Holds state flags for the element. Created only when a state-setting method is invoked.
    """

    def __init__(self):
        self.element_states: ElementStates | None = None

    def add_conditional_disabled(self, is_disabled: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is disabled (non-interactive).

        Args:
            is_disabled (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when the element should be disabled.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(is_disabled)
        if self.element_states.is_disabled is None:
            self.element_states.is_disabled = []
        self.element_states.is_disabled.append(condition)

    def add_permission_disabled(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is disabled.

        Args:
            is_base_user (bool): If True, the element is disabled for base users
                (non-advanced users). If False, the element is disabled for advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_disabled is None:
            self.element_states.is_disabled = []
        self.element_states.is_disabled.append(condition)

    def add_conditional_required(self, is_required: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is required for valid form submission.

        Args:
            is_required (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when the element is required.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(is_required)
        if self.element_states.is_required is None:
            self.element_states.is_required = []
        self.element_states.is_required.append(condition)

    def add_permission_required(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is required.

        Args:
            is_base_user (bool): If True, the element is required for base users
                (non-advanced users). If False, the element is required for advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_required is None:
            self.element_states.is_required = []
        self.element_states.is_required.append(condition)

    def add_conditional_read_only(self, is_read_only: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is read-only (not editable).

        Args:
            is_read_only (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when the element should be read-only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(is_read_only)
        if self.element_states.is_read_only is None:
            self.element_states.is_read_only = []
        self.element_states.is_read_only.append(condition)

    def add_permission_read_only(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is read-only.

        Args:
            is_base_user (bool): If True, the element is read-only for base users
                (non-advanced users). If False, the element is read-only for advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_read_only is None:
            self.element_states.is_read_only = []
        self.element_states.is_read_only.append(condition)

    def add_conditional_error(self, is_error: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is in an error state.

        Args:
            is_error (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when the element should show an error state.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(is_error)
        if self.element_states.is_error is None:
            self.element_states.is_error = []
        self.element_states.is_error.append(condition)

    def add_permission_error(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is in an error state.

        Args:
            is_base_user (bool): If True, the element shows an error state for base users
                (non-advanced users). If False, the element shows an error state for advanced
                users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_error is None:
            self.element_states.is_error = []
        self.element_states.is_error.append(condition)

    def add_conditional_warning(self, is_warning: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is in a warning state.

        Args:
            is_warning (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when the element should show a warning state.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(is_warning)
        if self.element_states.is_warning is None:
            self.element_states.is_warning = []
        self.element_states.is_warning.append(condition)

    def add_permission_warning(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is in a warning state.

        Args:
            is_base_user (bool): If True, the element shows a warning state for base users
                (non-advanced users). If False, the element shows a warning state for advanced
                users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_warning is None:
            self.element_states.is_warning = []
        self.element_states.is_warning.append(condition)

    def add_conditional_success(self, is_success: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is in a success state.

        Args:
            is_success (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when the element should show a success state.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(is_success)
        if self.element_states.is_success is None:
            self.element_states.is_success = []
        self.element_states.is_success.append(condition)

    def add_permission_success(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is in a success state.

        Args:
            is_base_user (bool): If True, the element shows a success state for base users
                (non-advanced users). If False, the element shows a success state for advanced
                users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_success is None:
            self.element_states.is_success = []
        self.element_states.is_success.append(condition)

    def add_conditional_hidden(self, is_hidden: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is hidden in the UI.

        Args:
            is_hidden (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when the element should be hidden.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(is_hidden)
        if self.element_states.is_hidden is None:
            self.element_states.is_hidden = []
        self.element_states.is_hidden.append(condition)

    def add_permission_hidden(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is hidden.

        Args:
            is_base_user (bool): If True, the element is hidden from base users
                (non-advanced users). If False, the element is hidden from advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_hidden is None:
            self.element_states.is_hidden = []
        self.element_states.is_hidden.append(condition)

    def add_conditional_info(self, is_info: Field | Parameter | Calculation | bool):
        """
        Sets whether the element is in an info state.

        Args:
            is_info (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when the element should show an info state.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(is_info)
        if self.element_states.is_info is None:
            self.element_states.is_info = []
        self.element_states.is_info.append(condition)

    def add_permission_info(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether the element is in an info state.

        Args:
            is_base_user (bool): If True, the element shows an info state for base users
                (non-advanced users). If False, the element shows an info state for advanced
                users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.is_info is None:
            self.element_states.is_info = []
        self.element_states.is_info.append(condition)

    def add_conditional_reserve_space(self, reserve_space: Field | Parameter | Calculation | bool):
        """
        Sets whether space is reserved in the layout when the element is hidden.

        Args:
            reserve_space (Field | Parameter | Calculation | bool):
                Condition that evaluates to ``True`` when space should be reserved.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = get_boolean_condition(reserve_space)
        if self.element_states.reserve_space is None:
            self.element_states.reserve_space = []
        self.element_states.reserve_space.append(condition)

    def add_permission_reserve_space(self, is_base_user: bool):
        """
        Adds a permission-based condition controlling whether space is reserved when the element
        is hidden.

        Args:
            is_base_user (bool): If True, space is reserved for base users
                (non-advanced users). If False, space is reserved for advanced users only.
        """
        if self.element_states is None:
            self.element_states = ElementStates()
        condition = ModelPermissionsCondition(is_advanced_user=not is_base_user)
        if self.element_states.reserve_space is None:
            self.element_states.reserve_space = []
        self.element_states.reserve_space.append(condition)


@typechecked
class Element(BaseElement):
    """
    Base class for all UI elements.

    Attributes:
        property_field_mapping:
            Mapping between UI element properties and the underlying
            model or data field names that supply their values.
        hidden:
            Indicates whether the element should be initially hidden.
        size:
            Optional hint for how large the UI element should appear.
    """

    #: The properties of this element whose value may be driven per-row by a field/named value,
    #: mapped to the data type that value must resolve to. Keys are the camelCase property names;
    #: this is both the allowlist and the type spec. Empty on the base (nothing mappable);
    #: subclasses override. ``TextInput``/``DateTimePicker`` compute it from instance state via
    #: :meth:`_property_types`.
    #:
    #: TODO: the platform also allows mapping fixed-set properties (enums such as fontWeight,
    #: variant, layoutStyle, display; icon-subset/id fields such as iconSet, defaults, iconSource;
    #: and STRING_ARRAY fields such as swatchColors). They are excluded for now because an
    #: arbitrary bound value can't be guaranteed to be a valid member of the fixed set; add them
    #: back once we validate the bound value against the allowed set.
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {}

    def __init__(self, hidden: bool | None = None, size: ElementSize | None = None):
        super().__init__()
        self.hidden = hidden
        self.size = size
        self.tooltip: str | None = None
        self.property_field_mapping: dict[str, str] = {}

    def _property_types(self) -> dict[str, DataType]:
        """The mappable properties for *this* element. Overridden where the set depends on
        instance state (e.g. a multiline :class:`TextInput`, a :class:`DateTimePicker` mode)."""
        return type(self).PROPERTY_TYPES

    def add_property_field_mapping(
        self, property_name: str, value: Field | Parameter | Calculation | TemplateBindingKey
    ) -> "Element":
        """
        Drive a supported property of this element from a field, parameter, or calculation.

        Only a fixed set of properties can be mapped per element, each expecting a specific data
        type (see :attr:`PROPERTY_TYPES`). A :class:`TemplateBindingKey` (a list-template
        placeholder) is accepted without a type check, since its value is resolved later.

        Args:
            property_name: The camelCase property to drive (e.g. ``"backgroundColor"``).
            value: The field, named value, calculation, or template placeholder supplying it.

        Raises:
            ValueError: If the property is not mappable on this element, or the value's data type
                does not match the property's expected type.
        """
        supported = self._property_types()
        if property_name not in supported:
            if not supported:
                raise ValueError(
                    f"{type(self).__name__} has no mappable properties; "
                    f"cannot map {property_name!r}."
                )
            raise ValueError(
                f"Unsupported property {property_name!r} for {type(self).__name__}. "
                f"Supported properties are: {', '.join(sorted(supported))}."
            )
        if not isinstance(value, TemplateBindingKey):
            expected = supported[property_name]
            actual = value.to_data_type()
            if actual != expected:
                raise ValueError(
                    f"Property {property_name!r} on {type(self).__name__} expects a "
                    f"{expected.value} value, but {value.id} is {actual}."
                )
        self.property_field_mapping[property_name] = value.to_string()
        return self


@dataclass
@typechecked
class ElementContainer(Element):
    """
    A UI element that groups and contains one or more child UI elements.
    Containers allow hierarchical UI layouts where multiple elements are
    visually or logically grouped together.

    Attributes:
        elements:
            The list of child UI elements contained within this container.
    """

    elements: list[Element] = field(default_factory=list)

    def __post_init__(self):
        super().__init__()

    def add_element(self, element: Element) -> None:
        """
        Adds a child UI element to the container.

        Args:
            element (Element):
                The UI element to add as a child of this container.
        """
        self.elements.append(element)


@typechecked
class InputElement(Element):
    """
    Base class for editable elements that bind to and write a model value.

    An ``InputElement`` resolves its ``data_source`` (a ``Field``, ``Parameter``,
    ``Calculation``, or ``ContextVariable``) to a :class:`ModelVariable`, validates that the
    source's data type is one the element supports, and automatically wires any validation
    rules attached to the bound field or named value into conditional error/warning/info states
    (with a tooltip pointing at the validation message).

    Because inputs are first-class :class:`Element`\\s, they may be placed anywhere an element is
    accepted — inside form cells, cards, containers, or list templates.

    Attributes:
        supported_data_types (frozenset[DataType]):
            The data types this element may bind to. Enforced in ``__init__`` for
            ``Field``/``Parameter``/``Calculation`` sources; context variables are not type
            checked. Subclasses override this.
        data_source (ModelVariable | None):
            The resolved model variable backing the element's value.
        object_field_reference (str | None):
            For an OBJECT-typed data source, the field of the referenced table to edit.
        default_value_reference (DefaultValueReference | None):
            A field/named-value/baseline the element can reset its value to.
        data_validation_rule (DataValidationRule | None):
            A list or range validation rule applied to user input.
        on_change (ModelEvent | None):
            An editor event run when the user changes the value, instead of the element writing
            its own bound value.
    """

    supported_data_types: frozenset[DataType] = frozenset()

    def __init__(
        self,
        data_source: DataSource,
        *,
        object_field_reference: str | None = None,
    ):
        super().__init__()
        # An already-resolved ModelVariable (e.g. a context-variable reference built by a form
        # adder) is passed through verbatim: it carries no static type, so there is nothing to
        # type-check or wire validation states for. Likewise, when an object_field_reference is
        # given the bound value is an OBJECT and the edited field's type lives on the referenced
        # table — not statically visible here — so the supported-type check is skipped.
        if isinstance(data_source, ModelVariable):
            self.data_source: ModelVariable | None = data_source
        else:
            if object_field_reference is None:
                self._assert_supported(data_source)
            self.data_source = get_model_variable(data_source)
        self.object_field_reference = object_field_reference
        self.default_value_reference: DefaultValueReference | None = None
        self.data_validation_rule: DataValidationRule | None = None
        self.on_change: ModelEvent | None = None
        self.display_format: str | None = None
        if not isinstance(data_source, ModelVariable):
            self._wire_validation_states(data_source)

    def supports_list_validation(self) -> bool:
        """Whether :meth:`set_list_validation` applies to this element. Overridden per subclass."""
        return False

    def _assert_supported(
        self, data_source: Field | Parameter | Calculation | ContextVariable
    ) -> None:
        """Assert the bound source's data type is one this element supports.

        Context variables carry no static type and are not checked. Subclasses binding to
        OBJECT values (e.g. :class:`Dropdown`) override this rather than using
        ``supported_data_types`` (there is no ``DataType.OBJECT`` member — object values are
        :class:`ObjectDataType` instances).
        """
        if not self.supported_data_types:
            return
        if not isinstance(data_source, Field | Parameter | Calculation):
            return
        data_type = data_source.to_data_type()
        if data_type not in self.supported_data_types:
            raise ValueError(
                f"{type(self).__name__} does not support data type {data_type}; "
                f"supported: {sorted(t.value for t in self.supported_data_types)}"
            )

    def _wire_validation_states(
        self, data_source: Field | Parameter | Calculation | ContextVariable
    ) -> None:
        """Wire a bound field's/named value's validation rules into conditional states + tooltip.

        Lifted from the former ``FormView._set_element_states`` so the behaviour travels with the
        element regardless of where it is used.
        """
        if isinstance(data_source, NamedValue):
            validation_values = data_source.get_validation_values()
            if validation_values and isinstance(validation_values, list):
                for validation_value in validation_values:
                    self.tooltip = f"${{{validation_value.message_value.to_string()}}}"
                    if validation_value.severity == Severity.INFO:
                        self.add_conditional_info(validation_value.invalid_value)
                    if validation_value.severity == Severity.WARNING:
                        self.add_conditional_warning(validation_value.invalid_value)
                    if validation_value.severity in (Severity.CRITICAL, Severity.ERROR):
                        self.add_conditional_error(validation_value.invalid_value)
        elif isinstance(data_source, Field):
            validation_fields = data_source.get_validation_fields()
            if validation_fields and isinstance(validation_fields, list):
                for validation_field in validation_fields:
                    self.tooltip = f"${{{validation_field.message_field.to_string()}}}"
                    if validation_field.severity == Severity.INFO:
                        self.add_conditional_info(validation_field.invalid_field)
                    if validation_field.severity == Severity.WARNING:
                        self.add_conditional_warning(validation_field.invalid_field)
                    if validation_field.severity in (Severity.CRITICAL, Severity.ERROR):
                        self.add_conditional_error(validation_field.invalid_field)

    def set_default_value_reference(
        self,
        value: Field | Parameter | Calculation,
        behaviour: DefaultValueBehaviour = DefaultValueBehaviour.DEFAULT,
    ) -> "InputElement":
        """
        Set a reference value this element can reset to.

        Args:
            value: The default value source. A ``Field`` sets reference type FIELD; a
                ``Parameter``/``Calculation`` sets NAMED_VALUE.
            behaviour: Controls the behaviour of the default value override.
        """
        value_type = (
            DefaultValueType.FIELD if isinstance(value, Field) else DefaultValueType.NAMED_VALUE
        )
        self.default_value_reference = DefaultValueReference(value_type, value.id, behaviour)
        return self

    def set_baseline_reset(
        self,
        baseline: Baseline | str,
        behaviour: DefaultValueBehaviour = DefaultValueBehaviour.DEFAULT,
    ) -> "InputElement":
        """
        Show a reset icon that reverts this element to its value at a baseline.

        Args:
            baseline: The baseline to revert to, or its name.
            behaviour: Controls the reset behaviour.
        """
        baseline_name = baseline.name if isinstance(baseline, Baseline) else baseline
        self.default_value_reference = DefaultValueReference(
            DefaultValueType.BASELINE, baseline_name, behaviour
        )
        return self

    def set_list_validation(
        self, reference_field: Field | Parameter | Calculation
    ) -> "InputElement":
        """
        Restrict input to the values held in a referenced array.

        Args:
            reference_field: A field, parameter, or calculation whose value is an **array** of the
                allowed values (e.g. a ``STRING_ARRAY`` column). A scalar reference is rejected.

        Raises:
            ValueError: If this element does not support list validation, or ``reference_field``
                does not resolve to an array value.
        """
        if not self.supports_list_validation():
            raise ValueError(f"`set_list_validation` is not supported for {type(self).__name__}")
        if not reference_field.to_data_type().is_array():
            raise ValueError(
                f"`set_list_validation` requires an array reference holding the allowed values; "
                f"{reference_field.id} is {reference_field.to_data_type()}."
            )
        self.data_validation_rule = DataValidationRule(
            type=DataValidationType.LIST,
            reference_field=reference_field.id,
        )
        return self

    def set_range_validation(
        self,
        min_value: str | Value | None = None,
        max_value: str | Value | None = None,
        flag: ValidationFlag = ValidationFlag.INCLUSIVE,
    ) -> "InputElement":
        """
        Limit input to a numeric/temporal range.

        Args:
            min_value: Minimum. A ``Value`` is a literal bound; a ``str`` names a field/named value.
            max_value: Maximum. A ``Value`` is a literal bound; a ``str`` names a field/named value.
            flag: Whether the bounds are inclusive or exclusive.

        Raises:
            ValueError: If this element does not support range validation, or neither bound given.
        """
        if not isinstance(self, NumberInput | DateTimePicker):
            raise ValueError(f"`set_range_validation` is not supported for {type(self).__name__}")
        if min_value is None and max_value is None:
            raise ValueError("`set_range_validation` requires `min_value` or `max_value`")

        rule = DataValidationRule(type=DataValidationType.RANGE, flag=flag)
        if min_value is not None:
            if isinstance(min_value, Value):
                rule.min_value = min_value
            else:
                rule.min_value_column = min_value
        if max_value is not None:
            if isinstance(max_value, Value):
                rule.max_value = max_value
            else:
                rule.max_value_column = max_value

        self.data_validation_rule = rule
        return self

    def set_reference_field(self, field: str) -> "InputElement":
        """Sets the referenced-table field to edit for an OBJECT-type data source."""
        self.object_field_reference = field
        return self

    def set_display_format(self, display_format: str) -> "InputElement":
        """Sets the display format string for this element."""
        self.display_format = display_format
        return self

    def set_on_change_event(self, event: ModelEvent) -> "InputElement":
        """
        Run an editor event when the user changes this element's value.

        When set, the element no longer writes its own bound value on change; the event runs
        instead, receiving the picked value as its ``editorValue`` context entry.

        Raises:
            ValueError: If an on-change event has already been set.
        """
        if self.on_change is not None:
            raise ValueError("ERROR - on-change event has already been set")
        self.on_change = event
        return self


@dataclass
@typechecked
@json_type_info("container")
class Container(ElementContainer):
    """
    A layout container used to group UI elements together.

    Attributes:
        display:
            CSS display property for this container, either flex or grid.
        gap:
            Spacing between child elements. Applies to both row and column gaps for flex-based
            layouts.
        horizontal_alignment:
            Determines how child elements are aligned horizontally within the container.
    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "gap": DataType.STRING,
        "horizontalAlignment": DataType.STRING,
        "verticalAlignment": DataType.STRING,
    }

    display: ContainerType = ContainerType.FLEX
    gap: str | None = None
    horizontal_alignment: HorizontalAlignment | None = None


@dataclass
@typechecked
@json_type_info("card")
class Card(ElementContainer):
    """
    A UI card element that displays its child elements in either a list layout
    or a grid layout. Cards may have customisable styling, spacing, and
    interaction behaviour.
    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "backgroundColor": DataType.STRING,
        "borderColor": DataType.STRING,
        "hoverBackgroundColor": DataType.STRING,
        "hoverBorderColor": DataType.STRING,
        "leftAccent": DataType.STRING,
        "rightAccent": DataType.STRING,
        "rowCount": DataType.INTEGER,
    }

    # Layout configuration
    layout_style: LayoutStyle | None = None
    row_count: int | None = None
    grid_ordering: GridOrder | None = None
    column_ratio: str | None = None
    row_spacing: RowSpacing | None = None
    align_content: AlignContent | None = None
    compact: bool | None = None

    # Interaction
    on_click: ModelEvent | None = None
    on_click_key: TemplateBindingKey | None = None

    # Styling
    border_color: str | None = None
    border_left: str | None = None
    border_radius: str | None = None
    background_color: str | None = None
    left_accent: str | None = None
    right_accent: str | None = None
    hover_background_color: str | None = None
    hover_border_color: str | None = None
    column_background_color: str | None = None
    padding: str | None = None
    shadow: Shadow | None = None

    # Footer
    footer: Element | None = None


@dataclass
@typechecked
@json_type_info("badge")
class Badge(ElementContainer):
    """
    A small visual label used to display short status or metadata.

    Attributes:
        variant:
            Determines the visual style variant of the badge.
        background_color:
            CSS-compatible string specifying the badge's background colour.
        on_click:
            Action to perform when the badge is clicked.
        minimum_width:
            Minimum width for the badge, expressed in CSS-compatible units.
    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "backgroundColor": DataType.STRING,
        "minimumWidth": DataType.STRING,
    }

    variant: BadgeVariant | None = None
    background_color: str | None = None
    on_click: ModelEvent | None = None
    minimum_width: str | None = None


@dataclass
@typechecked
@json_type_info("overflow")
class OverflowElement(ElementContainer):
    """
    A container element that replaces overflowing items in a :class:`ListElement`
    when its ``overflow_strategy`` is set to :attr:`OverflowStrategy.SUMMARISE`.

    Instead of clipping or scrolling, the list renders this element once in place
    of all items that did not fit within the container's bounds. Populate it with
    any child elements to create a custom overflow summary — for example, a
    :class:`Text` label such as "+5 more" or an icon paired with a count.

    Example::

        overflow = OverflowElement()
        overflow.add_element(Text(value=overflow_count_field))

        employee_list = ListElement(
            data_source=employees_table,
            template=template_card,
            overflow_strategy=OverflowStrategy.SUMMARISE,
            overflow_element=overflow,  # Required when strategy is SUMMARISE
        )
    """

    _OVERFLOW_COUNT = "${overflowCount}"

    @property
    def overflow_count(self):
        return self._OVERFLOW_COUNT


@typechecked
@json_type_info("button")
class Button(Element):
    """
    A clickable button UI element.

    Attributes:
        text_value:
            The text displayed on the button.
        text_color:
            CSS-compatible string specifying the button's text colour.
        background_color:
            CSS-compatible string specifying the button's background colour.
        icon_source:
            Identifier for the icon to display, in DaitumIcon format.
        icon_color:
            CSS-compatible string specifying the colour of the icon.
        on_click_key:
            Optional key used for click event routing or analytics.
        on_click:
            The action to perform when the button is clicked.
    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "size": DataType.STRING,
        "textColor": DataType.STRING,
        "backgroundColor": DataType.STRING,
    }

    def __init__(
        self,
        text_value: str | Parameter | Calculation | Field | TemplateBindingKey | None = None,
        on_click: ModelEvent | None = None,
        on_click_key: TemplateBindingKey | None = None,
        icon_source: Icon | None = None,
    ):
        super().__init__()

        if isinstance(text_value, str):
            self.text_value: str | None = text_value
        elif text_value:
            self.text_value = f"${{{text_value.to_string()}}}"
        else:
            self.text_value = None
        self.text_color: str | None = None
        self.background_color: str | None = None
        self.icon_source = icon_source
        self.icon_color: str | None = None
        self.on_click_key = on_click_key
        self.on_click = on_click

    def set_text_color(self, text_color: str) -> "Button":
        """Sets the CSS text colour of the button."""
        self.text_color = text_color
        return self

    def set_background_color(self, background_color: str) -> "Button":
        """Sets the CSS background colour of the button."""
        self.background_color = background_color
        return self

    def set_icon_color(self, icon_color: str) -> "Button":
        """Sets the CSS colour of the button icon."""
        self.icon_color = icon_color
        return self


@typechecked
def get_model_variable(
    variable: Field | Parameter | Calculation | ContextVariable,
) -> ModelVariable | None:
    """
    Converts a model-related object into a ModelVariable descriptor.

    Parameters:
        variable:
            A Field, Parameter, Calculation, or ContextVariable instance
            representing a model value used by UI elements.

    Returns:
        ModelVariable (Optional):
            A standardised wrapper describing the variable type
            (FIELD, NAMED_VALUE, or CONTEXT_VARIABLE) and its identifier.

    Notes:
        - Field → ModelVariableType.FIELD (uses field_id)
        - Parameter or Calculation → ModelVariableType.NAMED_VALUE (uses named_value_id)
        - ContextVariable → ModelVariableType.CONTEXT_VARIABLE (uses id)
    """
    if isinstance(variable, Field):
        return ModelVariable(ModelVariableType.FIELD, variable.id)

    if isinstance(variable, Parameter | Calculation):
        return ModelVariable(ModelVariableType.NAMED_VALUE, variable.id)

    if isinstance(variable, ContextVariable):
        return ModelVariable(ModelVariableType.CONTEXT_VARIABLE, variable.id)

    return None


@typechecked
@json_type_info("checkbox")
class Checkbox(InputElement):
    """
    A standard checkbox bound to a boolean value.

    Attributes:
        on_check:
            Event triggered when the checkbox transitions to the checked state.
        on_uncheck:
            Event triggered when the checkbox transitions to the unchecked state.
        data_source:
            Model variable that stores the current value of the checkbox.
    """

    supported_data_types = frozenset({DataType.BOOLEAN})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {"size": DataType.STRING}

    def __init__(
        self, data_source: Field | Parameter | Calculation | ContextVariable | ModelVariable
    ):
        super().__init__(data_source)
        self.on_check: ModelEvent | None = None
        self.on_uncheck: ModelEvent | None = None

    def set_on_event(self, event: ModelEvent) -> "Checkbox":
        """Assigns the event fired when the checkbox transitions into the checked state."""
        self.on_check = event
        return self

    def set_off_event(self, event: ModelEvent) -> "Checkbox":
        """Assigns the event fired when the checkbox transitions into the unchecked state."""
        self.on_uncheck = event
        return self


@dataclass
@typechecked
@json_type_info("icon")
class IconElement(Element):
    """
    Represents an icon UI element.

    Attributes:
        icon_source:
            The icon to display. The string uses the DaitumIcon format, which is a string of the
            form "iconFamily.ICON".
        color:
            The CSS-compatible colour to render the icon.
        on_click:
            Event triggered when the icon is clicked.
        tooltip:
            Optional tooltip displayed when the user hovers over the icon.
    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "color": DataType.STRING,
        "size": DataType.STRING,
        "tooltip": DataType.STRING,
    }

    icon_source: Icon | None = None
    color: str | None = None
    on_click: ModelEvent | None = None
    tooltip: str | None = None

    def __post_init__(self):
        # Capture the dataclass-assigned tooltip before Element.__init__ resets it to None.
        tooltip = self.tooltip
        super().__init__()
        self.tooltip = tooltip


@typechecked
@json_type_info("iconCheckbox")
class IconCheckbox(InputElement):
    """
    A checkbox that uses icons to represent its checked and unchecked states.

    Attributes:
        on_check:
            Event triggered when the checkbox transitions to the checked state.
        on_uncheck:
            Event triggered when the checkbox transitions to the unchecked state.
        data_source:
            Model variable storing the current checkbox value.
        off_icon:
            Icon displayed when the checkbox is unchecked.
        on_icon:
            Icon displayed when the checkbox is checked.
        show_background:
            Whether a background is drawn behind the icon. Defaults to ``False``.
    """

    supported_data_types = frozenset({DataType.BOOLEAN})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {"size": DataType.STRING}

    def __init__(
        self,
        data_source: Field | Parameter | Calculation | ContextVariable | ModelVariable,
        off_icon: IconConfig,
        on_icon: IconConfig,
    ):
        super().__init__(data_source)
        self.on_check: ModelEvent | None = None
        self.on_uncheck: ModelEvent | None = None
        self.show_background: bool = False
        self.off_icon = off_icon
        self.on_icon = on_icon

    def set_on_event(self, event: ModelEvent) -> "IconCheckbox":
        """Assigns the event fired when the icon checkbox transitions into the on state."""
        self.on_check = event
        return self

    def set_off_event(self, event: ModelEvent) -> "IconCheckbox":
        """Assigns the event fired when the icon checkbox transitions into the off state."""
        self.on_uncheck = event
        return self

    def set_show_background(self, show: bool = True) -> "IconCheckbox":
        """Sets whether a background is drawn behind the icon."""
        self.show_background = show
        return self


@typechecked
@json_type_info("reviewRating")
class ReviewRating(InputElement):
    """
    A review rating component (filled and empty icons) bound to a numeric value.

    Attributes:
        fill_icon:
            Icon configuration used to display the "filled" (selected) rating value.
        empty_icon:
            Icon configuration used to display the "empty" (unselected) rating value.
        data_source:
            Model variable storing the current rating value (e.g., 1–5 stars).
        fill_color:
            Optional colour override for the filled icons.
    """

    supported_data_types = frozenset({DataType.INTEGER, DataType.DECIMAL})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "fillColor": DataType.STRING,
        "size": DataType.STRING,
    }

    def __init__(
        self,
        data_source: DataSource,
    ):
        super().__init__(data_source)
        self.fill_icon: IconConfig | None = None
        self.empty_icon: IconConfig | None = None
        self.fill_color: str | None = None

    def set_fill_icon(self, icon: IconConfig) -> "ReviewRating":
        """Sets the icon used for filled (selected) rating values."""
        self.fill_icon = icon
        return self

    def set_empty_icon(self, icon: IconConfig) -> "ReviewRating":
        """Sets the icon used for empty (unselected) rating values."""
        self.empty_icon = icon
        return self

    def set_fill_color(self, color: str) -> "ReviewRating":
        """Sets the colour override for filled rating icons."""
        self.fill_color = color
        return self


@typechecked
@json_type_info("slider")
class Slider(InputElement):
    """
    A slider (toggle switch) bound to a boolean value.

    Attributes:
        on_check:
            Event triggered when the slider moves into the on state.
        on_uncheck:
            Event triggered when the slider moves into the off state.
        data_source:
            Reference to a model variable that stores the slider's current value.
    """

    supported_data_types = frozenset({DataType.BOOLEAN})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {"size": DataType.STRING}

    def __init__(
        self, data_source: Field | Parameter | Calculation | ContextVariable | ModelVariable
    ):
        super().__init__(data_source)
        self.on_check: ModelEvent | None = None
        self.on_uncheck: ModelEvent | None = None

    def set_on_event(self, event: ModelEvent) -> "Slider":
        """Assigns the event fired when the slider transitions into the on state."""
        self.on_check = event
        return self

    def set_off_event(self, event: ModelEvent) -> "Slider":
        """Assigns the event fired when the slider transitions into the off state."""
        self.on_uncheck = event
        return self


@typechecked
@json_type_info("text")
class Text(Element):
    """
    A text UI element used for displaying static or dynamic textual content.

    Attributes:
        value:
            The string content to be displayed.
        color:
            Optional CSS-compatible colour for the text.
        font_weight:
            The thickness of the displayed text.
        variant:
            The presentation style of the text (inline or paragraph).
        show_tool_tip:
            Whether the text should display a tooltip containing its full value. Useful when the
            displayed text is too long and may be truncated, but the user still needs access to
            the complete, non-truncated content.
        wrap:
            Whether the text should wrap onto multiple lines when it exceeds the available
            width. Defaults to ``False``, keeping the text on a single line (which may be
            truncated); enable via :meth:`set_wrap`.
    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "color": DataType.STRING,
        "size": DataType.STRING,
        "showTooltip": DataType.BOOLEAN,
        "wrap": DataType.BOOLEAN,
        "noWrap": DataType.BOOLEAN,
    }

    def __init__(  # noqa: PLR0913
        self,
        value: str | Parameter | Calculation | Field | TemplateBindingKey | None = None,
        color: str | None = None,
        font_weight: FontWeight | None = None,
        variant: TextVariant | None = None,
        show_tool_tip: bool = False,
        *,
        data_source: Field | Parameter | Calculation | ContextVariable | None = None,
    ):
        super().__init__()

        if isinstance(value, str):
            self.value: str | None = value
        elif value is not None:
            self.value = f"${{{value.to_string()}}}"
        else:
            self.value = None
        self.color = color
        self.font_weight = font_weight
        self.variant = variant
        self.show_tool_tip = show_tool_tip
        self.wrap = False
        self.data_source = get_model_variable(data_source) if data_source is not None else None
        self.object_field_reference: str | None = None

    def set_reference_field(self, field: str) -> "Text":
        """Sets the referenced-table field to display for an OBJECT-type data source."""
        self.object_field_reference = field
        return self

    def set_color(self, color: str) -> "Text":
        """Sets the CSS colour for this text element."""
        self.color = color
        return self

    def set_font_weight(self, weight: FontWeight) -> "Text":
        """Sets the font weight for this text element."""
        self.font_weight = weight
        return self

    def set_variant(self, variant: TextVariant) -> "Text":
        """Sets the presentation variant (inline or paragraph) for this text element."""
        self.variant = variant
        return self

    def set_wrap(self, wrap: bool) -> "Text":
        """Sets whether the text wraps onto multiple lines when it exceeds the available width."""
        self.wrap = wrap
        return self


@typechecked
@json_type_info("list")
class ListElement(Element):
    """
    A display element that renders every row of a data table using a reusable
    element template.

    For each row in the source table, the template is instantiated and its
    placeholder values are resolved via field bindings. Placeholders are
    declared inside the template using :class:`TemplateBindingKey`; bindings
    are registered with :meth:`add_template_field_mapping`, which maps each
    placeholder key to the corresponding field in the source table.

    Attributes:
        data_source (ModelVariable | None):
            Model variable referencing the data source. Set when a Field or
            NamedValue is provided; ``None`` when a Table is provided directly.
        source_table (str | None):
            ID of the source table. Set when a Table is provided; ``None``
            when a Field or NamedValue is provided instead.
        template (Optional[Element]):
            The element used as a template for each row.
        field_bindings (dict[str, str]):
            Resolved mapping from placeholder names to source table field IDs.
            Populated by :meth:`add_template_field_mapping`; do not set directly.
        layout_direction (LayoutDirection):
            The direction in which rendered items are arranged.
            ``COLUMN`` stacks items vertically (default);
            ``ROW`` places them horizontally.
        wrap (Optional[bool]):
            When ``True``, items wrap onto new lines when the container width
            is exceeded. When ``False`` or ``None``, items are clipped or
            scrollable depending on the container.
        overflow_strategy (OverflowStrategy):
            Defines strategies for handling content that exceeds the bounds of
            its container.
        width (Optional[str]):
            Defines width of the list element.
        height (Optional[str]):
            Defines height of the list element.
        overflow_element (Optional[OverflowElement]):
            Element rendered in place of overflowing items when
            ``overflow_strategy`` is :attr:`OverflowStrategy.SUMMARISE`. Required
            when strategy is ``SUMMARISE``; may also be supplied via
            :meth:`set_overflow_element`.
        row_gap (Optional[str]):
            Vertical spacing between rows.
        column_gap (Optional[str]):
            Horizontal spacing between columns.

    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "layoutDirection": DataType.STRING,
        "wrap": DataType.BOOLEAN,
        "overflowStrategy": DataType.STRING,
        "height": DataType.STRING,
        "width": DataType.STRING,
        "rowGap": DataType.STRING,
        "columnGap": DataType.STRING,
    }

    def __init__(
        self,
        data_source: Table | Field | NamedValue,
        template: Element,
        layout_direction: LayoutDirection = LayoutDirection.COLUMN,
        overflow_strategy: OverflowStrategy = OverflowStrategy.SCROLL,
        overflow_element: "OverflowElement | None" = None,
    ):
        super().__init__()

        if isinstance(data_source, NamedValue | Field):
            datatype = data_source.to_data_type()
            if not (isinstance(datatype, ObjectDataType) and datatype.is_array()):
                raise ValueError(f"Data source must be an object-array type, got {datatype}")

        self.data_source: ModelVariable | None = None
        self.source_table: str | None = None

        if isinstance(data_source, Field | NamedValue):
            self.data_source = get_model_variable(data_source)
        elif isinstance(data_source, Table):
            self.source_table = data_source.id

        if overflow_strategy == OverflowStrategy.SUMMARISE and overflow_element is None:
            raise ValueError("overflow_element is required when overflow_strategy is SUMMARISE.")

        self.template = template
        self.field_bindings: dict[str, str] = {}
        self.layout_direction = layout_direction
        self.wrap: bool = False
        self.overflow_strategy = overflow_strategy
        self.height: str | None = None
        self.width: str | None = None
        self.overflow_element: OverflowElement | None = overflow_element
        self.row_gap: str | None = None
        self.column_gap: str | None = None

    def set_wrap(self, wrap: bool) -> "ListElement":
        """Sets whether items wrap onto multiple lines."""
        self.wrap = wrap
        return self

    def set_size(self, height: str | None = None, width: str | None = None) -> "ListElement":
        """Sets the height and/or width of the list element."""
        self.height = height
        self.width = width
        return self

    def set_overflow_element(self, overflow_element: OverflowElement) -> "ListElement":
        """Sets the element rendered in place of overflowing items when strategy is SUMMARISE."""
        if self.overflow_strategy != OverflowStrategy.SUMMARISE:
            raise ValueError(
                "overflow_element is only applicable when overflow_strategy is SUMMARISE."
            )
        self.overflow_element = overflow_element
        return self

    def set_gap(self, gap: str | None = None, cross_axis_gap: str | None = None) -> "ListElement":
        """
        Sets the gap between items in the list.

        Args:
            gap: Spacing along the main axis direction.
            cross_axis_gap: Spacing along the cross axis direction.
        """
        if gap is not None or cross_axis_gap is not None:
            if self.layout_direction == LayoutDirection.ROW:
                self.column_gap = gap
                self.row_gap = cross_axis_gap
            else:
                self.row_gap = gap
                self.column_gap = cross_axis_gap
        return self

    def add_template_field_mapping(self, key: TemplateBindingKey, field: Field) -> None:
        """
        Registers a binding between a template placeholder and a source table field.

        Each call adds one entry to ``field_bindings``. The placeholder declared
        by ``key`` inside the template will be substituted with the value of
        ``field`` for each rendered row.

        Args:
            key (TemplateBindingKey):
                The placeholder key referenced inside the template via
                :class:`TemplateBindingKey`. Must match exactly the key used
                when constructing the template elements.
            field (Field):
                The source table field whose value replaces the placeholder
                at render time.

        Example::
            name_key = TemplateBindingKey("name")
            employee_list.add_template_field_mapping(name_key, name_field)
        """
        self.field_bindings[key.to_string()] = field.to_string()


@typechecked
@json_type_info("modelEditorLink")
class ModelEditorLink(Element):
    """
    A hyperlink element that opens the Daitum model editor.

    Renders as a clickable text link. The model and scenario to open can be
    bound to ``Field``, ``Parameter``, ``Calculation``, or ``ContextVariable``
    values so they are resolved at runtime.

    Attributes:
        text_value (str):
            The visible label of the link. Accepts a static string or a
            model-variable reference rendered as ``${...}``. Defaults to
            ``"Open Model"``.
        destination (ModelEditorLinkDestination):
            The model-editor destination built from the provided ``model_id``,
            ``scenario_id``, and ``open_new_tab`` arguments.
    """

    def __init__(
        self,
        model_id: Field | Parameter | Calculation | ContextVariable,
        scenario_id: Field | Parameter | Calculation | ContextVariable | None = None,
        text_value: str | Parameter | Calculation | Field | TemplateBindingKey = "Open Model",
        open_new_tab: bool = False,
    ):
        super().__init__()

        if isinstance(text_value, str):
            self.text_value: str = text_value
        else:
            self.text_value = f"${{{text_value.to_string()}}}"

        self.destination = ModelEditorLinkDestination(model_id, scenario_id, open_new_tab)


@typechecked
@json_type_info("textInput")
class TextInput(InputElement):
    """
    A text input bound to a ``STRING`` value.

    Renders as a single-line field by default. Supplying ``rows`` (and optionally ``resize``)
    turns it into a multiline text area.

    Attributes:
        default_value (StringValue | None): Text pre-filled when the bound value is absent.
        rows (int | None): Visible row count; set to make the input a multiline text area.
        resize (TextInputResize | None): User-resizability direction for the text area.
    """

    supported_data_types = frozenset({DataType.STRING})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {"size": DataType.STRING}

    def __init__(
        self,
        data_source: DataSource,
        default_value: StringValue | None = None,
        rows: int | None = None,
        resize: TextInputResize | None = None,
    ):
        super().__init__(data_source)
        self.default_value = default_value
        self.rows = rows
        self.resize = resize

    def _property_types(self) -> dict[str, DataType]:
        # rows/resize only apply to a multiline (rows-set) text area.
        if self.rows is None:
            return self.PROPERTY_TYPES
        return {**self.PROPERTY_TYPES, "rows": DataType.INTEGER, "resize": DataType.STRING}


@typechecked
@json_type_info("numberInput")
class NumberInput(InputElement):
    """
    A numeric input bound to an ``INTEGER`` or ``DECIMAL`` value.

    Supports list and range validation.

    Attributes:
        default_value (IntegerValue | DecimalValue | None): Numeric default pre-filled when the
            bound value is absent.
    """

    supported_data_types = frozenset({DataType.INTEGER, DataType.DECIMAL})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "size": DataType.STRING,
        "displayFormat": DataType.STRING,
    }

    def __init__(
        self,
        data_source: DataSource,
        default_value: IntegerValue | DecimalValue | None = None,
    ):
        super().__init__(data_source)
        self.default_value = default_value

    def supports_list_validation(self) -> bool:
        return True


@typechecked
@json_type_info("dropdown")
class Dropdown(InputElement):
    """
    A dropdown (select) bound to an ``OBJECT`` value.

    Displays a list of object references from the bound table. The display label defaults to the
    referenced table's key column; override with :meth:`set_display_field`. Supports list
    validation to restrict available choices.

    Attributes:
        choices (ModelVariable | None): Optional model variable supplying an alternative choice
            list.
        searchable (bool): If ``True``, includes a search box within the dropdown.
        nullable (bool): If ``True``, allows the value to be cleared to null.
        object_reference_display_field (str | None): Field to display for each object choice.
    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "size": DataType.STRING,
        "isSearchable": DataType.BOOLEAN,
        "isNullable": DataType.BOOLEAN,
        "isClearable": DataType.BOOLEAN,
        "placeholder": DataType.STRING,
    }

    def __init__(
        self,
        data_source: DataSource,
        *,
        object_reference_display_field: str | None = None,
    ):
        super().__init__(data_source)
        self.choices: ModelVariable | None = None
        self.searchable: bool = False
        self.nullable: bool = False
        # Default the display field to the referenced table's key column when derivable, so the
        # frontend always has a label to render for each choice.
        if object_reference_display_field is None and isinstance(
            data_source, Field | Parameter | Calculation
        ):
            data_type = data_source.to_data_type()
            if isinstance(data_type, ObjectDataType):
                source_table = cast(Table, data_type._source_table)  # noqa: SLF001
                object_reference_display_field = source_table.key_column
        if object_reference_display_field is None:
            raise ValueError(
                "Dropdown requires an object_reference_display_field (the field to show for each "
                "choice); it could not be derived from the data source's referenced table key."
            )
        self.object_reference_display_field = object_reference_display_field

    def _assert_supported(
        self, data_source: Field | Parameter | Calculation | ContextVariable
    ) -> None:
        if not isinstance(data_source, Field | Parameter | Calculation):
            return
        data_type = data_source.to_data_type()
        if not isinstance(data_type, ObjectDataType) or data_type.is_array():
            raise ValueError(f"Dropdown must bind to a non-array OBJECT value; got {data_type}.")

    def set_display_field(self, field: str) -> "Dropdown":
        """Sets the field to display for each object choice."""
        self.object_reference_display_field = field
        return self

    def set_searchable(self, searchable: bool) -> "Dropdown":
        """Sets whether the dropdown includes a search box."""
        self.searchable = searchable
        return self

    def set_nullable(self, nullable: bool) -> "Dropdown":
        """Sets whether the dropdown value may be cleared to null."""
        self.nullable = nullable
        return self

    def set_choices(self, choices: ModelVariable) -> "Dropdown":
        """Sets the model variable providing the list of available choices."""
        self.choices = choices
        return self


@typechecked
@json_type_info("dateTimePicker")
class DateTimePicker(InputElement):
    """
    A date, time, or date-time picker bound to a ``DATE``, ``TIME``, or ``DATETIME`` value.

    The ``mode`` selects which portion is edited. Supports list and range validation.

    Attributes:
        mode (DateTimeMode): Which portion of the value is edited.
        with_selector (bool): If ``True``, displays an inline calendar selector.
        time_interval (int | None): Minute increment for the time portion.
    """

    supported_data_types = frozenset({DataType.DATE, DataType.TIME, DataType.DATETIME})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "size": DataType.STRING,
        "displayFormat": DataType.STRING,
    }

    def __init__(
        self,
        data_source: DataSource,
        mode: DateTimeMode = DateTimeMode.DATE_TIME,
        *,
        object_field_reference: str | None = None,
    ):
        super().__init__(data_source, object_field_reference=object_field_reference)
        self.mode = mode
        self.with_selector: bool | None = None
        self.time_interval: int | None = None

    def _property_types(self) -> dict[str, DataType]:
        types = dict(self.PROPERTY_TYPES)
        if self.mode in (DateTimeMode.DATE, DateTimeMode.DATE_TIME):
            types["withSelector"] = DataType.BOOLEAN
        if self.mode in (DateTimeMode.TIME, DateTimeMode.DATE_TIME):
            types["timeInterval"] = DataType.INTEGER
        return types

    def supports_list_validation(self) -> bool:
        return True

    def set_mode(self, mode: DateTimeMode) -> "DateTimePicker":
        """Sets which portion of the value (date, time, or both) is edited."""
        self.mode = mode
        return self

    def set_with_selector(self, with_selector: bool) -> "DateTimePicker":
        """Sets whether an inline calendar selector is shown."""
        self.with_selector = with_selector
        return self

    def set_time_interval(self, minutes: int) -> "DateTimePicker":
        """Sets the minute increment for the time portion."""
        self.time_interval = minutes
        return self


@typechecked
@json_type_info("colorPicker")
class ColorPicker(InputElement):
    """
    A colour picker bound to a ``STRING`` value (typically a hex colour).

    Attributes:
        swatch_colors (list[str] | None): Palette restricting selectable colours; when omitted the
            UI may use its default theme palette.
        allow_custom (bool | None): Whether free-form hex entry is allowed.
    """

    supported_data_types = frozenset({DataType.STRING})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "size": DataType.STRING,
        "allowCustom": DataType.BOOLEAN,
        "placeholder": DataType.STRING,
    }

    def __init__(
        self,
        data_source: DataSource,
    ):
        super().__init__(data_source)
        self.swatch_colors: list[str] | None = None
        self.allow_custom: bool | None = None

    def set_swatch_colors(self, colors: list[str]) -> "ColorPicker":
        """Sets the palette of swatch colours available in the picker."""
        self.swatch_colors = colors
        return self

    def set_allow_custom(self, allow: bool) -> "ColorPicker":
        """Sets whether free-form hex colour entry is allowed."""
        self.allow_custom = allow
        return self


@typechecked
@json_type_info("iconPicker")
class IconPicker(InputElement):
    """
    An icon picker bound to a ``STRING`` value (an icon identifier).

    Attributes:
        icon_set (IconSet): Which icon catalogue to show.
        defaults (list[str] | None): Icon ids shown first in the picker.
        preview_color (str | None): CSS colour used to tint icons in the dropdown.
    """

    supported_data_types = frozenset({DataType.STRING})
    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "size": DataType.STRING,
        "previewColor": DataType.STRING,
        "placeholder": DataType.STRING,
    }

    def __init__(
        self,
        data_source: DataSource,
        icon_set: IconSet = IconSet.ALL,
    ):
        super().__init__(data_source)
        self.icon_set = icon_set
        self.defaults: list[Icon] | None = None
        self.preview_color: str | None = None

    def set_icon_set(self, icon_set: IconSet) -> "IconPicker":
        """Sets the icon catalogue to display in the picker."""
        self.icon_set = icon_set
        return self

    def set_defaults(self, defaults: list[Icon]) -> "IconPicker":
        """Sets the icons displayed first in the picker."""
        self.defaults = defaults
        return self

    def set_preview_color(self, color: str) -> "IconPicker":
        """Sets the CSS colour used to tint icons in the picker dropdown."""
        self.preview_color = color
        return self


@typechecked
@json_type_info("array")
class ArrayElement(InputElement):
    """
    Shows and edits the value of an ARRAY-typed field, named value or context variable as one
    element.

    Whether it can be edited comes from its element states, as for any :class:`InputElement`.
    Unlike :class:`ListElement`, which lays out a template element once per row of an
    OBJECT_ARRAY, this shows the values themselves.

    Attributes:
        layout (ArrayLayout): How the values are laid out.
        object_reference_display_field (str | None): For an OBJECT_ARRAY, the field of the
            referenced table each value is shown by. Defaults to the referenced table's key column.
        placeholder (str | None): Text shown when the array is empty.
        allow_duplicates (bool): Whether the same value may be added twice. Defaults to ``False``:
            adding a duplicate is refused, and any the value already holds are marked.
        allow_blanks (bool): Whether a blank (null) keeps its place in the array. Defaults to
            ``False``: blanks are not shown, clearing a value removes it, and an edit writes the
            array back without them.
    """

    PROPERTY_TYPES: ClassVar[dict[str, DataType]] = {
        "displayFormat": DataType.STRING,
        "placeholder": DataType.STRING,
        "allowDuplicates": DataType.BOOLEAN,
        "allowBlanks": DataType.BOOLEAN,
    }

    def __init__(
        self,
        data_source: DataSource,
        layout: ArrayLayout = ArrayLayout.BADGE,
        *,
        object_reference_display_field: str | None = None,
    ):
        super().__init__(data_source)
        self.layout = layout
        if object_reference_display_field is None and isinstance(
            data_source, Field | Parameter | Calculation
        ):
            data_type = data_source.to_data_type()
            if isinstance(data_type, ObjectDataType):
                source_table = cast(Table, data_type._source_table)  # noqa: SLF001
                object_reference_display_field = source_table.key_column
        self.object_reference_display_field = object_reference_display_field
        self.placeholder: str | None = None
        self.allow_duplicates: bool = False
        self.allow_blanks: bool = False

    def _assert_supported(
        self, data_source: Field | Parameter | Calculation | ContextVariable
    ) -> None:
        if not isinstance(data_source, Field | Parameter | Calculation):
            return
        data_type = data_source.to_data_type()
        if not data_type.is_array():
            raise ValueError(f"ArrayElement must bind to an ARRAY value; got {data_type}.")

    def set_layout(self, layout: ArrayLayout) -> "ArrayElement":
        """Sets how the values are laid out."""
        self.layout = layout
        return self

    def set_display_field(self, field: str) -> "ArrayElement":
        """Sets the referenced-table field each value of an OBJECT_ARRAY is shown by."""
        self.object_reference_display_field = field
        return self

    def set_placeholder(self, placeholder: str) -> "ArrayElement":
        """Sets the text shown when the array is empty."""
        self.placeholder = placeholder
        return self

    def set_allow_duplicates(self, allow: bool = True) -> "ArrayElement":
        """Sets whether the same value may be added twice."""
        self.allow_duplicates = allow
        return self

    def set_allow_blanks(self, allow: bool = True) -> "ArrayElement":
        """Sets whether a blank (null) keeps its place in the array."""
        self.allow_blanks = allow
        return self


#: Sizes a :class:`RangeBar` supports: the thin bar (SMALL) and the bordered bar (LARGE).
RANGE_BAR_SIZES = (ElementSize.SMALL, ElementSize.LARGE)

_NUMERIC_TYPES = frozenset({DataType.INTEGER, DataType.DECIMAL})
_NUMERIC_ARRAY_TYPES = frozenset({DataType.INTEGER_ARRAY, DataType.DECIMAL_ARRAY})


@typechecked
@json_type_info("rangeBar")
class RangeBar(Element):
    """
    A read-only bar from ``min`` to ``max`` that shows a value against coloured ranges.

    The error, warning, success and info ranges are drawn as bands in that state's background
    colour, and the value is drawn as a fill from ``min`` or as a marker, in the colour of the
    range it lands in. The bar has no input, no click behaviour and no label.

    Every property is a model variable, read at render time. Each range is a numeric array of
    inclusive ``[from, to]`` pairs, e.g. ``[0, 5, 7, 10]`` is 0–5 and 7–10. A single value is
    open-ended: on its own it covers everything up to it; among other ranges it opens towards
    the side with no other range. Overlaps resolve error > warning > success > info.

    With no ranges, the element's state (:meth:`add_conditional_error` and friends) colours the
    whole bar. When ranges are given they decide the colours.

    Attributes:
        value:
            The value shown on the bar (``INTEGER`` or ``DECIMAL``).
        min:
            The start of the scale. Defaults to 0 when unset.
        max:
            The end of the scale. Defaults to 100 when unset.
        error_ranges, warning_ranges, success_ranges, info_ranges:
            ``INTEGER_ARRAY`` or ``DECIMAL_ARRAY`` values of ``[from, to]`` pairs.
        indicator:
            A ``STRING`` value holding ``"FILL"`` (the default) or ``"MARKER"``.
    """

    def __init__(
        self,
        value: DataSource,
        min_value: DataSource | None = None,
        max_value: DataSource | None = None,
    ):
        super().__init__()
        self.value = self._variable(value, _NUMERIC_TYPES)
        self.min = self._variable(min_value, _NUMERIC_TYPES)
        self.max = self._variable(max_value, _NUMERIC_TYPES)
        self.error_ranges: ModelVariable | None = None
        self.warning_ranges: ModelVariable | None = None
        self.success_ranges: ModelVariable | None = None
        self.info_ranges: ModelVariable | None = None
        self.indicator: ModelVariable | None = None

    def set_error_ranges(self, ranges: DataSource) -> "RangeBar":
        """Sets the numeric array of ``[from, to]`` pairs drawn as error ranges."""
        self.error_ranges = self._variable(ranges, _NUMERIC_ARRAY_TYPES)
        return self

    def set_warning_ranges(self, ranges: DataSource) -> "RangeBar":
        """Sets the numeric array of ``[from, to]`` pairs drawn as warning ranges."""
        self.warning_ranges = self._variable(ranges, _NUMERIC_ARRAY_TYPES)
        return self

    def set_success_ranges(self, ranges: DataSource) -> "RangeBar":
        """Sets the numeric array of ``[from, to]`` pairs drawn as success ranges."""
        self.success_ranges = self._variable(ranges, _NUMERIC_ARRAY_TYPES)
        return self

    def set_info_ranges(self, ranges: DataSource) -> "RangeBar":
        """Sets the numeric array of ``[from, to]`` pairs drawn as info ranges."""
        self.info_ranges = self._variable(ranges, _NUMERIC_ARRAY_TYPES)
        return self

    def set_indicator(self, indicator: DataSource) -> "RangeBar":
        """Sets the ``STRING`` value holding ``"FILL"`` or ``"MARKER"``."""
        self.indicator = self._variable(indicator, frozenset({DataType.STRING}))
        return self

    def set_size(self, size: ElementSize) -> "RangeBar":
        """
        Sets the bar size: ``ElementSize.SMALL`` (the default) or ``ElementSize.LARGE``.

        Raises:
            ValueError: If ``size`` is any other ``ElementSize``.
        """
        if size not in RANGE_BAR_SIZES:
            raise ValueError(f"Invalid size for RangeBar: {size.value}. Use SMALL or LARGE.")
        self.size = size
        return self

    @staticmethod
    def _variable(
        source: DataSource | None, supported: frozenset[DataType]
    ) -> ModelVariable | None:
        """Resolve ``source``, checking a field's or named value's data type is ``supported``.

        Raises:
            ValueError: If the source's data type is not one of ``supported``.
        """
        if source is None or isinstance(source, ModelVariable):
            return source
        if isinstance(source, Field | Parameter | Calculation):
            data_type = source.to_data_type()
            if data_type not in supported:
                raise ValueError(
                    f"RangeBar does not support data type {data_type} for {source.id}; "
                    f"supported: {sorted(t.value for t in supported)}"
                )
        return get_model_variable(source)
