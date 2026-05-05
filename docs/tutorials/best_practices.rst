Best Practices
==============

Recommendations for writing maintainable, correct, and performant Daitum models.

.. note::
   This tutorial is a work in progress. Full content coming soon.

Code Organisation
-----------------

- Keep model definition, UI definition, and configuration in separate modules.
- Use descriptive names for tables and fields — these appear in the platform UI.
- Extract shared formula logic into named formula functions.

Testing
-------

- Write unit tests against ``.to_dict()`` output to catch serialisation regressions.
- Test edge cases in calculated fields with boundary input values.

Versioning
----------

- Follow semantic versioning: increment the minor version for new fields or views,
  the major version for breaking schema changes.
- Always update the changelog before releasing to production.
