# daitum-model

Model and formula generation library for the [Daitum](https://daitum.com) optimisation platform.

`daitum-model` provides a fluent builder API for defining optimisation models: tables, fields,
formulas, and formula functions. The model is serialised to JSON and packaged for upload to the
Daitum platform.

## Installation

```bash
pip install daitum-model
```

## Usage

```python
from daitum_model import ModelBuilder, DataType
from daitum_model import formulas

model = ModelBuilder()
table = model.add_table("locations")
table.add_data_field("id", DataType.INTEGER)
table.add_data_field("name", DataType.STRING)
```

## Documentation

Full documentation is available at [daitum-core.readthedocs.io](https://daitum-core.readthedocs.io).

## Changelog

See [CHANGELOG.md](https://github.com/daitumapi/daitum-core/blob/main/daitum-model/CHANGELOG.md) for version history.

## Licence

Apache 2.0 — see [LICENSE](https://github.com/daitumapi/daitum-core/blob/main/LICENSE).
