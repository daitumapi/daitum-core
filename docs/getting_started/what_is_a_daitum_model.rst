What is a Daitum Model?
=======================

A Daitum model is a complete, programmatic description of an optimisation application.

It defines what data to use, how the problem is solved, and how results are presented —
all written in Python and serialised to JSON for execution on the Daitum platform.

The three parts
---------------

A Daitum model is composed of three artefacts, each built with a dedicated library:

**Model definition** (``daitum_model``)
    Defines the data structures and core logic of the problem.

    - **Tables** — named collections of records (e.g. ``Jobs``, ``Machines``)
    - **Fields** — typed columns within a table (``STRING``, ``DECIMAL``, ``DATETIME``, …)
    - **Calculations** — derived values at the model level (e.g. total cost)
    - **Parameters** — user-editable scalar inputs (e.g. a budget limit)

**UI definition** (``daitum_ui``)
    Defines the user interface presented in the platform.

    - **Views** — tables, Gantt charts, forms, cards, maps, and more
    - **Navigation** — navigation structure linking views
    - **Context variables** — shared runtime state (filters, toggles)

**Configuration** (``daitum_configuration``)
    Defines how the optimisation is executed and data is transformed.

    - **Algorithm** — the solving approach (e.g. Genetic Algorithm, VNS)
    - **Optimisation model** — decision variables, objectives, and constraints
    - **Data sources** — input data mappings, data transforms, report properties

How the parts fit together
--------------------------

The three artefacts share a common object model. Tables and fields defined in
``daitum_model`` are referenced directly in the UI and configuration layers.

This allows a single definition (e.g. a field) to be reused across:
- UI components (columns, charts)
- optimisation logic (decision variables, constraints)
- calculations and outputs

.. code-block:: text

   daitum_model  ──────────────┐
        │  Tables, Fields,     ├──► Packaged and deployed to Daitum
        │  Calculations        │
        ▼                      │
   daitum_ui                   │
        │  Views, Navigation   │
        ▼                      │
   daitum_configuration        │
           Algorithm, Data ────┘

Deployment
----------

Each artefact is serialised to a Python ``dict`` and written to JSON.
These files are bundled into a ZIP archive and uploaded to the Daitum platform.

See the :doc:`quickstart` for a complete end-to-end example.