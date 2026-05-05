Installation
============

Requirements
------------

- Python 3.10 or later
- pip

Install Daitum
--------------

The recommended way to install Daitum is via the ``daitum-core`` meta-package:

.. code-block:: bash

   pip install daitum-core

``daitum-core`` is a convenience package that installs the full SDK, including:

- ``daitum_model`` — model and formula definition
- ``daitum_ui`` — UI definition
- ``daitum_configuration`` — algorithm and data source configuration

Install Specific Version
------------------------

To install a specific version of the SDK:

.. code-block:: bash

   pip install daitum-core==<version>

For example:

.. code-block:: bash

   pip install daitum-core==1.2.0

It is recommended to pin versions in production environments to ensure reproducibility.

Install Individual Packages
---------------------------

If you only need part of the SDK, you can install packages independently:

.. code-block:: bash

   pip install daitum-model
   pip install daitum-ui
   pip install daitum-configuration

You are responsible for managing version compatibility when installing packages individually.

Upgrade
-------

To upgrade to the latest version:

.. code-block:: bash

   pip install --upgrade daitum-core