Gantt View Types
================

Gantt view types define how time-based tasks are arranged and grouped
along a timeline. Each view type offers a different way of organising
tasks, depending on whether they are flat, categorised, or hierarchical.

All Gantt view types are created via :class:`UiBuilder` and share a common
set of configuration options, such as task definitions, dependencies,
and interaction behaviour.

The following Gantt view types are available:

* **GanttView** — a standard, flat Gantt layout where each task is rendered
  on its own row. This view is suitable when tasks do not need to be grouped
  or nested.
* **CategoryGanttView** — groups tasks by a category field, allowing multiple
  tasks to be displayed on the same category row. This is useful for visualising
  tasks that belong to logical groups such as teams, resources, or work streams.
* **TreeGridGanttView** — displays tasks in a hierarchical tree structure,
  supporting parent–child relationships between tasks. This view is ideal
  for project plans with nested tasks or multi-level breakdowns.

.. autoclass:: daitum_ui.gantt_view.GanttView
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.gantt_view.CategoryGanttView
    :no-index:
    :members:
    :show-inheritance:

.. autoclass:: daitum_ui.gantt_view.TreeGridGanttView
    :no-index:
    :members:
    :show-inheritance:
