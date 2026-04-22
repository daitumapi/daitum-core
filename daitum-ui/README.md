# daitum-ui

UI definition generation library for the [Daitum](https://daitum.com) optimisation platform.

`daitum-ui` provides a fluent builder API for defining UI screens, navigation groups, and
components. The UI definition is serialised to JSON and packaged for upload to the Daitum platform.

## Installation

```bash
pip install daitum-ui
```

## Usage

```python
from daitum_ui.ui_builder import UiBuilder

builder = UiBuilder()
nav = builder.add_navigation_group("Results")
```

## Documentation

Full documentation is available at [daitum-core.readthedocs.io](https://daitum-core.readthedocs.io).

## Changelog

See [CHANGELOG.md](https://github.com/daitumapi/daitum-core/blob/main/daitum-ui/CHANGELOG.md) for version history.

## Licence

Apache 2.0 — see [LICENSE](https://github.com/daitumapi/daitum-core/blob/main/LICENSE).
