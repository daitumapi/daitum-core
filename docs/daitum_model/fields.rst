Fields
======

Fields are the columns of a table. Every field has an id, a data type, and
optional :class:`~daitum_model.validator.Validator` instances. Three concrete
field types differ in where the value comes from:

- :class:`~daitum_model.fields.DataField` — imported data, with an optional
  default value.
- :class:`~daitum_model.fields.CalculatedField` — value computed by a
  :class:`~daitum_model.Formula`.
- :class:`~daitum_model.fields.ComboField` — carries both a formula and a
  stored value; the :attr:`~daitum_model.fields.ComboField.calculate_in_optimiser`
  flag decides whether the optimiser evaluates the formula
  (``True``) or reads the stored value (``False``). The opposite mode is used
  outside optimisation, e.g. when the field is rendered in the UI.

.. automodule:: daitum_model.fields
   :exclude-members: ValidationFieldsContainer
