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

Provides the ``Modal`` class, a container that wraps a single view as an overlay
with configurable action buttons (Close, Cancel, Save, Reset, Delete) and custom
footer elements. Adding a Save, Cancel, Reset, or Delete button switches the modal
into edit-dialog mode for transactional editing; titles may be static strings or
driven by a ``ContextVariable``.

Example:
    >>> builder = UiBuilder()
    >>> edit_view = builder.add_form_view(display_name="Edit Form")
    >>> edit_modal = builder.add_modal(
    ...     view=edit_view, height="500px", width="700px", title="Edit Customer"
    ... )
    >>> edit_modal.add_save_button()
    >>> edit_modal.add_cancel_button()
"""

from typeguard import typechecked

from daitum_ui._buildable import Buildable
from daitum_ui._ids import new_id
from daitum_ui.base_view import BaseView
from daitum_ui.context_variable import ContextVariable
from daitum_ui.elements import Button, Element
from daitum_ui.icons import Icon
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
        self.id: str = new_id()
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
        icon_source: Icon | None = None,
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
        icon_source: Icon | None = None,
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
        icon_source: Icon | None = None,
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
        icon_source: Icon | None = None,
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
        icon_source: Icon | None = None,
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
