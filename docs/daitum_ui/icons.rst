Icons
=====

.. automodule:: daitum_ui.icons
    :no-index:
    :members:
    :show-inheritance:

Examples
--------

Using icons with ``IconConfig``:

.. code-block:: python

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

Using outlined icons for inactive states:

.. code-block:: python

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

Using domain-specific icons:

.. code-block:: python

    # Child care activity icons
    swimming_icon = IconConfig(source=Icon.SWIMMING, color="#2196f3")
    programming_icon = IconConfig(source=Icon.PROGRAMMING, color="#9c27b0")
    study_icon = IconConfig(source=Icon.STUDY, color="#ff5722")

    # Staff qualification icons
    qualified_icon = IconConfig(source=Icon.QUALIFIED, color="#4caf50")
    first_aid_icon = IconConfig(source=Icon.FIRST_AID, color="#f44336")

Using selection icons:

.. code-block:: python

    # For icon checkbox states
    from daitum_ui.styles import IconCheckboxEditor

    checkbox_editor = IconCheckboxEditor(
        on_icon=IconConfig(source=Icon.SELECTED, color="#2196f3"),
        off_icon=IconConfig(source=Icon.UNSELECTED, color="#9e9e9e")
    )

Using action icons in buttons:

.. code-block:: python

    from daitum_ui.elements import Button

    # Save button with paper plane icon
    save_button = Button(text_value="Send", icon_source=Icon.PAPER_PLANE)

    # Edit button with pen icon
    edit_button = Button(text_value="Edit", icon_source=Icon.PEN_TO_SQUARE)

Using compliance and validation icons:

.. code-block:: python

    # WWCC validation status
    valid_wwcc = IconConfig(source=Icon.WWCC_VALID, color="#4caf50")
    invalid_wwcc = IconConfig(source=Icon.WWCC_INVALID, color="#f44336")

    # General validation check
    validation_check = IconConfig(source=Icon.CHECK, color="#4caf50")

Using information and help icons:

.. code-block:: python

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

Using NULL icon for conditional display:

.. code-block:: python

    # Show icon only when condition is met
    conditional_icon = IconConfig(
        source=Icon.CHECK if is_valid else Icon.NULL,
        color="#4caf50"
    )

Using navigation icons:

.. code-block:: python

    # Login/Logout
    login_icon = IconConfig(source=Icon.RIGHT_TO_BRACKET, color="#4caf50")
    logout_icon = IconConfig(source=Icon.RIGHT_FROM_BRACKET, color="#f44336")

    # Home navigation
    home_icon = IconConfig(source=Icon.HOUSE, color="#2196f3")

Using lock status icons:

.. code-block:: python

    # Locked state
    locked_icon = IconConfig(source=Icon.LOCK, color="#f44336")

    # Unlocked state
    unlocked_icon = IconConfig(source=Icon.LOCK_OPEN, color="#4caf50")

Using array editor icons:

.. code-block:: python

    # Row manipulation icons
    add_icon = IconConfig(source=Icon.ADD_ROW, color="#4caf50")
    remove_icon = IconConfig(source=Icon.REMOVE_ROW, color="#f44336")
    move_icon = IconConfig(source=Icon.MOVE_ROW, color="#2196f3")
