# spdx-storage

> Store, query, import, and export [SPDX](https://spdx.dev/) data across a range of graph database systems.

<!-- [![PyPI version](https://img.shields.io/pypi/v/spdx-storage.svg)](https://pypi.org/project/spdx-storage/) -->
<!-- [![Python versions](https://img.shields.io/pypi/pyversions/spdx-storage.svg)](https://pypi.org/project/spdx-storage/) -->
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

`spdx-storage` is a Python library for persisting [SPDX](https://spdx.dev/) (Software Package
Data Exchange) data in graph databases. SPDX data is inherently a graph of software components,
relationships, licenses, and provenance, which makes graph databases a natural fit for storing,
linking, and querying it.

The library offers a single, backend-agnostic interface so you can **import** SPDX documents into a
graph store, work with the data, and **export** it back out to standard SPDX serializations, without
tying your code to any one database system.

> **Project status:** Early development. The package is under active construction and the public
> API illustrated below is subject to change before the first stable release.

## Features

- **Graph-native storage** for SPDX data, built on top of `triplestore`.
- **Pluggable backends** &mdash; target several graph database systems through one consistent API.
- **Import** SPDX documents from standard serializations into a graph store.
- **Export** stored data back out to standard SPDX serializations.
- **Backend-agnostic code** &mdash; switch databases without rewriting your application.
- **Typed** &mdash; ships with type hints (`py.typed`) for a great editor and type-checker experience.

## Installation

`spdx-storage` requires a recent version of Python. Development is happening on **Python 3.14+**.

```bash
pip install spdx-storage
```

Or, using [uv](https://docs.astral.sh/uv/):

```bash
uv add spdx-storage
```

## Quick start

The API below is illustrative and will be refined as the library is implemented.

```python
from spdx_storage import SPDXStore

# Open (or create) a graph-backed store using a connection string.
with SPDXStore.connect("jena", {"graph": "http://localhost/jena"} ) as store:
    # Import SPDX data from a file into the graph store.
    store.import_file("example.spdx.json")

    # ... query, traverse, or merge documents in the store ...

    # Export the stored data back out to an SPDX serialization.
    store.export_file("export.spdx.json", format="json-ld")
```

## Supported backends

`spdx-storage` is designed around a pluggable backend architecture, so the same code can target
different graph database systems by changing only the connection string. Planned and candidate
backends will be listed here.

## About SPDX

[SPDX](https://spdx.dev/) is an open international standard, for communicating
software bill of materials (SBOM) information, including components, licenses, copyrights,
and security references. Learn more:

- [SPDX website](https://spdx.dev/)
- [SPDX specification](https://spdx.github.io/spdx-spec/)

## Development

This project uses [uv](https://docs.astral.sh/uv/) for environment and dependency management and
[ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Clone the repository
git clone https://github.com/spdx/spdx-storage.git
cd spdx-storage

# Create the environment and install dependencies
uv sync

# Lint and format (must be done before committing)
uv run ruff check .
uv run ruff format .
```

## Roadmap

- [ ] Core SPDX graph model and storage interface
- [ ] Import from standard SPDX serializations
- [ ] Export to standard SPDX serializations
- [ ] Documentation and usage guides

## License

This project is licensed under the **Apache License 2.0**.
See the [LICENSE](LICENSE) file for the full text.

Note that this repository may include content developed with support
from one or more generative artificial intelligence solutions.
