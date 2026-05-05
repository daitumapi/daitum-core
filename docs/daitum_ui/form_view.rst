Form View
=========

Form view components for the UI Generator framework.

This module provides comprehensive form-building capabilities through the FormView class
and a rich collection of form elements. Forms are structured layouts for data entry,
editing, and display, organized in a flexible grid-based system with powerful data
binding and validation features.

Enums:
    - FormSize: Element sizing (EXTRA_SMALL, SMALL, MEDIUM, LARGE, EXTRA_LARGE, FIT_WIDTH)
    - FormVariant: Label styling variants (REGULAR, HEADER)
    - FormResize: Text area resize behavior (NONE, BOTH, HORIZONTAL, VERTICAL)
    - FormIconSet: Icon catalogue for icon pickers (ALL, DAITUM, FONT_AWESOME, FA_PRO)

Classes:
    - FormElement: Base class for all form elements with layout and validation
    - FormView: Container view managing form layout and elements
    - FormLabel, FormTextInput, FormNumberInput, FormBasicTextArea: Text elements
    - FormCheckbox, FormSlider, FormIconCheckbox: Boolean input elements
    - FormDropdown: Object selection element
    - FormDatePicker, FormTimePicker, FormDateTimePicker: Date/time elements
    - FormButton: Action button element
    - FormReviewRating: Rating input element
    - FormColourPickerInput: Colour (hex) picker
    - FormIconPicker: Icon selection picker

Example:
    >>> # Define data source
    >>> customers_table = Table("customers")
    >>>
    >>> # Create form view
    >>> builder = UiBuilder()
    >>> form = builder.add_form_view(
    ...     display_name="Customer Details",
    ...     total_rows=6,
    ...     table=customers_table,
    ...     match_row=MatchRowFilterMode.FIRST_ROW
    ... )
    >>>
    >>> # Configure form columns
    >>> form.set_columns(num_columns=2, width="250px")
    >>>
    >>> # Add form elements
    >>> # Header label
    >>> form.add_label(
    ...     text="Customer Information",
    ...     row=1, column=1, column_span=2,
    ...     variant=FormVariant.HEADER,
    ...     size=FormSize.LARGE
    ... )
    >>>
    >>> # Text inputs
    >>> name_label = form.add_label("Name:", row=2, column=1)
    >>> name_input = form.add_text_input(
    ...     text=Field("customer_name", DataType.STRING),
    ...     row=2, column=2
    ... )
    >>>
    >>> email_label = form.add_label("Email:", row=3, column=1)
    >>> email_input = form.add_text_input(
    ...     text=Field("email", DataType.STRING),
    ...     row=3, column=2
    ... )
    >>>
    >>> # Number input with validation
    >>> age_label = form.add_label("Age:", row=4, column=1)
    >>> age_input = form.add_number_input(
    ...     value=Field("age", DataType.INTEGER),
    ...     row=4, column=2
    ... )
    >>> age_input.set_range_validation(min_value=18, max_value=120)

.. autoclass:: daitum_ui.form_view.FormView
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormSize
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormVariant
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormResize
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormIconSet
    :no-index:
    :members:
    :show-inheritance:

Form Elements
-------------

Form elements are interactive components that can be placed inside a
:class:`FormView`. All form_view elements inherit from :class:`FormElement`.

.. autoclass:: daitum_ui.form_view.FormElement
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormLabel
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormTextInput
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormNumberInput
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormBasicTextArea
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormCheckbox
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormIconCheckbox
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormSlider
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormDropdown
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormDatePicker
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormTimePicker
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormDateTimePicker
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormButton
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormReviewRating
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormColourPickerInput
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.form_view.FormIconPicker
    :no-index:
    :members:
    :show-inheritance:

