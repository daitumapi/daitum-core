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
Modal dialog system for overlay views and transactional editing.

This module provides the Modal class, which creates modal dialog containers that
display views as overlays with pre-configured action buttons. Modals support
transactional editing workflows with automatic save, cancel, and reset functionality.

Main Components
---------------

**Modal Class:**
    Container that wraps a view and provides:

    - Configurable dimensions (width, height)
    - Static or dynamic titles
    - Pre-configured action buttons (Save, Cancel/Close, Reset, Delete)
    - Custom footer elements
    - Transaction-aware event handlers

**Button Types:**
    - Close Button: Non-transactional close (default)
    - Cancel Button: Transactional cancel with rollback
    - Save Button: Commit changes and close
    - Reset Button: Rollback and restart transaction
    - Delete Button: Custom destructive action

Modal Workflows
---------------

**Edit Dialog Mode (edit_dialog=True):**
    Activated when Save, Cancel, Reset, or Delete buttons are added.
    Supports transactional editing:

    - BEGIN transaction when modal opens (via show_modal_action)
    - SAVE: Commits transaction and closes modal
    - CANCEL: Rolls back transaction and closes modal
    - RESET: Rolls back and begins new transaction (keeps modal open)
    - DELETE: Custom event (typically includes transaction handling)

**View-Only Mode (edit_dialog=False):**
    Default mode with only Close button.
    No transaction management:

    - CLOSE: Simply closes modal without transaction operations
    - Used for information display, read-only views, or reports

Default Button Behaviors
-------------------------

**Close Button (default):**
    - Text: "Close"
    - Event: Rollback transaction + Close modal
    - Use: Non-editing dialogs or safe close

**Cancel Button:**
    - Text: "Cancel"
    - Event: Rollback transaction + Close modal
    - Use: Editing dialogs, discards changes
    - Sets edit_dialog=True

**Save Button:**
    - Text: "Save"
    - Event: Commit transaction + Close modal
    - Use: Editing dialogs, saves changes
    - Sets edit_dialog=True
    - Default styling: Blue background, white text

**Reset Button:**
    - Text: "Reset"
    - Event: Rollback transaction + Begin new transaction
    - Use: Editing dialogs, resets form to original values
    - Sets edit_dialog=True and show_reset_button=True
    - Keeps modal open for continued editing

**Delete Button:**
    - Text: "Delete"
    - Event: Must be provided (no default)
    - Use: Destructive operations
    - Sets edit_dialog=True
    - Default styling: Red background, white text
    - Requires custom event with transaction handling

Title Configuration
-------------------

Modals support two title modes:

**Static Title:**
    Fixed text displayed in modal header.
    Set by passing a string to the title parameter.

**Dynamic Title:**
    Title derived from ContextVariable value.
    Set by passing a ContextVariable to the title parameter.
    Useful for showing record-specific information (e.g., "Edit: John Doe").

Footer Customization
--------------------

In addition to pre-configured buttons, modals can have custom footer elements:

- Add any Element to the footer using add_footer()
- Footer elements appear alongside standard buttons
- Useful for additional actions, status indicators, or help text

Modal Identification
--------------------

Each modal receives a unique randomly-generated ID (16 ASCII characters).
This ID is used to reference the modal in show_modal_action() calls.

Examples
--------
Creating a simple view-only modal::

    # Create view and builder
    builder = UiBuilder()
    info_view = builder.add_form_view(display_name="Information")

    # Modal with just a close button (no transactions)
    info_modal = builder.add_modal(
        view=info_view,
        height="400px",
        width="600px",
        title="Information"
    )
    # Default close button is already configured

Creating an edit modal with save and cancel::

    # Create view
    edit_form_view = builder.add_form_view(display_name="Edit Form")

    # Modal for editing data (transactional)
    edit_modal = builder.add_modal(
        view=edit_form_view,
        height="500px",
        width="700px",
        title="Edit Customer"
    )

    # Add save button (commits changes)
    edit_modal.add_save_button()

    # Replace close with cancel button (discards changes)
    edit_modal.add_cancel_button()

Creating a modal with dynamic title::

    # Context variable for customer name
    customer_name_var = builder.add_context_variable(
        id="modal_title_name",
        type=CVType.STRING,
        default_value=""
    )

    # Create view
    customer_detail_view = builder.add_form_view(display_name="Customer Details")

    # Modal with dynamic title from context variable
    customer_modal = builder.add_modal(
        view=customer_detail_view,
        height="600px",
        width="800px",
        title=customer_name_var  # Title updates from context
    )
    customer_modal.add_save_button()
    customer_modal.add_cancel_button()

Creating a modal with reset button::

    # Create view
    data_entry_view = builder.add_form_view(display_name="Data Entry")

    # Edit modal with reset functionality
    form_modal = builder.add_modal(
        view=data_entry_view,
        height="450px",
        width="650px",
        title="Data Entry"
    )
    form_modal.add_save_button()
    form_modal.add_cancel_button()
    form_modal.add_reset_button()  # Allows user to reset form

Creating a modal with delete button::

    # Create delete event
    delete_event = ModelEvent()
    delete_event.add_begin_transaction()
    delete_event.add_delete_row_action(
        target_table=customers_table,
        row_count=1,
        select_mode=RowSelectionMode.INDEX,
        row=current_customer_context_var
    )
    delete_event.add_commit_transaction()
    delete_event.add_close_modal_action()

    # Create view
    delete_confirmation_view = builder.add_form_view(
        display_name="Delete Confirmation"
    )

    # Modal with delete functionality
    delete_modal = builder.add_modal(
        view=delete_confirmation_view,
        height="300px",
        width="500px",
        title="Confirm Delete"
    )
    delete_modal.add_delete_button(on_click=delete_event)
    delete_modal.add_cancel_button()

Customizing button appearance::

    # Create view
    custom_view = builder.add_form_view(display_name="Custom Form")

    # Modal with custom button styling
    styled_modal = builder.add_modal(
        view=custom_view,
        height="500px",
        width="700px",
        title="Custom Styling"
    )

    # Custom save button with icon and colors
    styled_modal.add_save_button(
        text_color="#ffffff",
        background_color="#4caf50",
        icon_source="FontAwesome.6.CHECK",
        icon_color="#ffffff"
    )

    # Custom cancel button
    styled_modal.add_cancel_button(
        text_color="#f44336",
        background_color="#ffebee"
    )

Creating a modal with custom events::

    # Custom save event with additional actions
    custom_save_event = ModelEvent()
    custom_save_event.add_commit_transaction()
    custom_save_event.add_run_data_source_action("refresh_list")
    custom_save_event.add_close_modal_action()
    custom_save_event.add_switch_view_action("list_view")

    # Create view
    form_view = builder.add_form_view(display_name="Form View")

    # Create modal with custom event
    custom_modal = builder.add_modal(
        view=form_view,
        height="500px",
        width="700px",
        title="Custom Save"
    )
    custom_modal.add_save_button(on_click=custom_save_event)
    custom_modal.add_cancel_button()

Adding custom footer elements::

    from daitum_ui.elements import Text

    # Create view
    complex_form_view = builder.add_form_view(display_name="Complex Form")

    # Modal with additional footer content
    help_modal = builder.add_modal(
        view=complex_form_view,
        height="600px",
        width="800px",
        title="Complex Form"
    )
    help_modal.add_save_button()
    help_modal.add_cancel_button()

    # Add help text to footer
    help_text = Text(
        value="* Required fields",
        color="#666666"
    )
    help_modal.add_footer(help_text)

Full-featured edit modal::

    # Create view
    comprehensive_edit_view = builder.add_form_view(
        display_name="Comprehensive Edit"
    )

    # Complete edit modal with all button types
    full_modal = builder.add_modal(
        view=comprehensive_edit_view,
        height="700px",
        width="900px",
        title="Edit Record"
    )

    # Primary action
    full_modal.add_save_button(
        background_color="#2196f3"
    )

    # Secondary actions
    full_modal.add_cancel_button()
    full_modal.add_reset_button()

    # Destructive action
    full_modal.add_delete_button(on_click=delete_event)

Opening a modal from an event::

    from daitum_ui.model_event import ModelEvent
    from daitum_ui.elements import Button

    # Event to show the modal
    show_edit_modal_event = ModelEvent()
    show_edit_modal_event.add_show_modal_action(
        modal_id=edit_modal.id,
        transactional=True  # Begins transaction automatically
    )

    # Attach to button click
    edit_button = Button(
        text_value="Edit",
        on_click=show_edit_modal_event
    )

Confirmation dialog pattern::

    # Create view
    confirmation_view = builder.add_form_view(
        display_name="Confirmation"
    )

    # Simple confirmation modal
    confirm_modal = builder.add_modal(
        view=confirmation_view,
        height="250px",
        width="450px",
        title="Confirm Action"
    )

    # Custom confirm event
    confirm_event = ModelEvent()
    confirm_event.add_commit_transaction()
    # ... add custom actions ...
    confirm_event.add_close_modal_action()

    confirm_modal.add_save_button(
        text_color="#ffffff",
        background_color="#f44336"
    )
    confirm_modal.save_button.text_value = "Confirm"  # Change button text

    confirm_modal.add_cancel_button()

Responsive modal sizing::

    # Create views
    large_view = builder.add_table_view(table=large_table)
    quick_action_view = builder.add_form_view(display_name="Quick Action")

    # Modal with percentage-based dimensions
    responsive_modal = builder.add_modal(
        view=large_view,
        height="80vh",  # 80% of viewport height
        width="90%",    # 90% of viewport width
        title="Large Modal"
    )
    responsive_modal.add_close_button()

    # Small modal for quick actions
    small_modal = builder.add_modal(
        view=quick_action_view,
        height="200px",
        width="400px",
        title="Quick Action"
    )
    small_modal.add_save_button()
    small_modal.add_cancel_button()
"""

import random
import string

from typeguard import typechecked

from daitum_ui._buildable import Buildable
from daitum_ui.base_view import BaseView
from daitum_ui.context_variable import ContextVariable
from daitum_ui.elements import Button, Element
from daitum_ui.model_event import ModelEvent


@typechecked
class Modal(Buildable):
    """
    Represents a modal dialog container that wraps a single view and provides
    configurable buttons such as Save, Cancel, Reset, and Delete.

    Attributes:
        view_id:
            The unique identifier of the view displayed inside the modal.
        height:
            A CSS height value.
        width:
            A CSS width value.
        title:
            Optional static title for the modal dialog.
        title_context_variable_id:
            ID of a `ContextVariable` used to dynamically render the title.
        close_button:
            The cancel/close button shown in the modal footer.
        save_button:
            The primary "Save" button shown in the modal footer.
        reset_button:
            Optional "Reset" button that can be configured and displayed when
            `show_reset_button` is True.
        delete_button:
            Optional "Delete" button for destructive operations.
        footer:
            A list of `Element` instances added to the modal footer.
        edit_dialog:
            Indicates whether this modal is used for editing existing records.
        show_reset_button:
            If True, the modal should display a reset button.
    """

    def __init__(
        self,
        view: BaseView,
        height: str,
        width: str,
        title: str | ContextVariable | None = None,
    ):
        """
        Args:
            view: The view displayed inside this modal.
            height: CSS height value (e.g. ``"500px"`` or ``"80vh"``).
            width: CSS width value (e.g. ``"700px"`` or ``"90%"``).
            title: Static title string, a ``ContextVariable`` for a dynamic title, or ``None``.
        """
        self.id: str = "".join(random.choices(string.ascii_letters, k=16))
        self.view_id = view.id
        self.height = height
        self.width = width

        if isinstance(title, ContextVariable):
            self.title = None
            self.title_context_variable_id: str | None = title.id
        else:
            self.title = title
            self.title_context_variable_id = None

        self.footer: list[Element] = []
        self.edit_dialog: bool = False
        self.show_reset_button: bool = False

        # Default ModelEvent for buttons
        self._close_event = ModelEvent()
        self._close_event.add_rollback_transaction()
        self._close_event.add_close_modal_action()

        self._save_event = ModelEvent()
        self._save_event.add_commit_transaction()
        self._save_event.add_close_modal_action()

        self._reset_event = ModelEvent()
        self._reset_event.add_rollback_transaction()
        self._reset_event.add_begin_transaction()

        self.close_button: Button | None = None
        self.save_button: Button | None = None
        self.reset_button: Button | None = None
        self.delete_button: Button | None = None

        self.add_close_button()

    def add_footer(self, element: Element) -> None:
        """
        Adds an element to the footer section of the modal.

        Args:
            element:
                A `daitum_ui.elements.Element` instance to append to the modal footer.
        """
        self.footer.append(element)

    def add_cancel_button(
        self,
        text_color: str | None = "black",
        background_color: str | None = "transparent",
        icon_source: str | None = None,
        icon_color: str | None = None,
        on_click: ModelEvent | None = None,
    ) -> Button:
        """
        Replaces and returns the modal's Close button.

        Args:
            text_color:
                Optional text colour for the button.
            background_color:
                Optional background colour.
            icon_source:
                Optional icon asset reference.
            icon_color:
                Optional icon colour.
            on_click:
                `ModelEvent` instance triggered when the button is clicked.

        Returns:
            The configured `Button` instance.
        """
        if on_click is None:
            on_click = self._close_event
        self.close_button = Button(
            text_value="Cancel",
            icon_source=icon_source,
            on_click=on_click,
        )
        if text_color is not None:
            self.close_button.set_text_color(text_color)
        if background_color is not None:
            self.close_button.set_background_color(background_color)
        if icon_color is not None:
            self.close_button.set_icon_color(icon_color)
        self.edit_dialog = True
        return self.close_button

    def add_close_button(
        self,
        text_color: str | None = "327BBF",
        background_color: str | None = "white",
        icon_source: str | None = None,
        icon_color: str | None = None,
        on_click: ModelEvent | None = None,
    ) -> Button:
        """
        Replaces and returns the modal's Close button.

        Args:
            text_color:
                Optional text colour for the button.
            background_color:
                Optional background colour.
            icon_source:
                Optional icon asset reference.
            icon_color:
                Optional icon colour.
            on_click:
                `ModelEvent` instance triggered when the button is clicked.

        Returns:
            The configured `Button` instance.
        """
        if on_click is None:
            on_click = self._close_event
        self.close_button = Button(
            text_value="Close",
            icon_source=icon_source,
            on_click=on_click,
        )
        if text_color is not None:
            self.close_button.set_text_color(text_color)
        if background_color is not None:
            self.close_button.set_background_color(background_color)
        if icon_color is not None:
            self.close_button.set_icon_color(icon_color)
        return self.close_button

    def add_save_button(
        self,
        text_color: str | None = "white",
        background_color: str | None = "#327BBF",
        icon_source: str | None = None,
        icon_color: str | None = None,
        on_click: ModelEvent | None = None,
    ) -> Button:
        """
        Replaces and returns the modal's Save button.

        Args:
            text_color:
                Optional text colour for the button.
            background_color:
                Optional background colour.
            icon_source:
                Optional icon asset reference.
            icon_color:
                Optional icon colour.
            on_click:
                `ModelEvent` instance triggered when the button is clicked.

        Returns:
            The configured `Button` instance.
        """

        if on_click is None:
            on_click = self._save_event

        self.save_button = Button(
            text_value="Save",
            icon_source=icon_source,
            on_click=on_click,
        )
        if text_color is not None:
            self.save_button.set_text_color(text_color)
        if background_color is not None:
            self.save_button.set_background_color(background_color)
        if icon_color is not None:
            self.save_button.set_icon_color(icon_color)
        self.edit_dialog = True
        return self.save_button

    def add_reset_button(
        self,
        text_color: str | None = "black",
        background_color: str | None = "transparent",
        icon_source: str | None = None,
        icon_color: str | None = None,
        on_click: ModelEvent | None = None,
    ) -> Button:
        """
        Creates and assigns a Reset button for the modal.

        Args:
            text_color:
                Optional text colour for the button.
            background_color:
                Optional background colour.
            icon_source:
                Optional icon asset reference.
            icon_color:
                Optional icon colour.
            on_click:
                `ModelEvent` instance triggered when the button is pressed.

        Returns:
            The configured `Button` instance.
        """

        if on_click is None:
            on_click = self._reset_event

        self.reset_button = Button(
            text_value="Reset",
            icon_source=icon_source,
            on_click=on_click,
        )
        if text_color is not None:
            self.reset_button.set_text_color(text_color)
        if background_color is not None:
            self.reset_button.set_background_color(background_color)
        if icon_color is not None:
            self.reset_button.set_icon_color(icon_color)
        self.show_reset_button = True
        self.edit_dialog = True
        return self.reset_button

    def add_delete_button(
        self,
        on_click: ModelEvent,
        text_color: str | None = "white",
        background_color: str | None = "red",
        icon_source: str | None = None,
        icon_color: str | None = None,
    ) -> Button:
        """
        Creates and assigns a Delete button for the modal.

        Args:
            text_color:
                Optional text colour for the button.
            background_color:
                Optional background colour.
            icon_source:
                Optional icon asset reference.
            icon_color:
                Optional icon colour.
            on_click:
                `ModelEvent` instance triggered when the button is clicked.

        Returns:
            The configured `Button` instance.
        """

        self.delete_button = Button(
            text_value="Delete",
            icon_source=icon_source,
            on_click=on_click,
        )
        if text_color is not None:
            self.delete_button.set_text_color(text_color)
        if background_color is not None:
            self.delete_button.set_background_color(background_color)
        if icon_color is not None:
            self.delete_button.set_icon_color(icon_color)

        self.edit_dialog = True
        return self.delete_button
