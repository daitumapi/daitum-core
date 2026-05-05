Gantt Task Definitions
======================

Gantt task definitions describe how rows from a source table are mapped
to tasks displayed on a Gantt timeline. They specify which fields provide
task identifiers, time ranges, display labels, and optional behavioural
information such as drag-and-drop or tooltips.

The following task definition types are available:

* **GanttTaskDefinition** — defines a standard, flat mapping where each
  table row corresponds to a single task on the timeline.
* **CategoryGanttTaskDefinition** — extends the base definition to support
  category-based grouping, allowing multiple tasks to appear under the
  same category row.
* **TreeGridGanttTaskDefinition** — defines hierarchical relationships
  between tasks, enabling parent–child structures in tree-grid Gantt views.

.. autoclass:: daitum_ui.gantt_view.GanttTaskDefinition
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.gantt_view.CategoryGanttTaskDefinition
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.gantt_view.TreeGridGanttTaskDefinition
    :no-index:
    :members:
    :show-inheritance:
