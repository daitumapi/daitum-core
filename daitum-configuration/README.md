# daitum-configuration

Model configuration generation library for the [Daitum](https://daitum.com) optimisation platform.

`daitum-configuration` provides a fluent builder API for defining model configurations: algorithms,
objectives, constraints, and data sources. The configuration is serialised to JSON and packaged
for upload to the Daitum platform.

## Installation

```bash
pip install daitum-configuration
```

## Usage

```python
from daitum_configuration import Configuration, GeneticAlgorithm

config = Configuration()
config.set_algorithm(GeneticAlgorithm())
```

## Documentation

Full documentation is available at [daitum-core.readthedocs.io](https://daitum-core.readthedocs.io).

## Changelog

See [CHANGELOG.md](https://github.com/daitumapi/daitum-core/blob/main/daitum-configuration/CHANGELOG.md) for version history.

## Licence

Apache 2.0 — see [LICENSE](https://github.com/daitumapi/daitum-core/blob/main/LICENSE).
