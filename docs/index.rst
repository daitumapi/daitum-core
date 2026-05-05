Daitum
======

**Daitum** is a platform for building and deploying optimisation applications.

It allows you to define data, business rules, optimisation logic, and user interfaces
in a single model, then deploy that model to a shared execution engine. The result is
a complete, configurable planning application without needing separate backend services
or frontends.

This documentation explains how to build, package, and deploy Daitum applications
using the Python SDK.

- Website: `daitum.com <https://daitum.com>`_
- Source: `github.com/daitumapi/daitum-core <https://github.com/daitumapi/daitum-core>`_

daitum-core
-----------

``daitum-core`` is the Python SDK for building Daitum applications.

Each application is defined by three parts:

- a **model** (data structures and logic)
- a **configuration** (algorithms, objectives, data sources)
- a **UI** (screens and components)

These are bundled into a deployable package and uploaded to the platform.

.. code-block:: bash

   pip install daitum-core

The SDK includes three main packages:

- :doc:`daitum_model/index` — define data structures and formulas
- :doc:`daitum_ui/index` — define screens and components
- :doc:`daitum_configuration/index` — define data sources and optimisation behaviour

.. toctree::
   :maxdepth: 1
   :caption: Getting Started

   getting_started/installation
   getting_started/what_is_a_daitum_model
   getting_started/quickstart

.. toctree::
   :maxdepth: 1
   :caption: Tutorials

   tutorials/introduction
   tutorials/data_stores
   tutorials/data_processors
   tutorials/reports
   tutorials/integration
   tutorials/templates_and_versioning
   tutorials/best_practices

.. toctree::
   :maxdepth: 2
   :caption: API Documentation

   daitum_model/index
   daitum_ui/index
   daitum_configuration/index
