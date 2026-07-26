# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from pathlib import Path

from rdflib import Graph
from spdx_storage.backends.base import StorageBackend


@dataclass
class ImportResult:
    """Information about an imported SPDX document."""

    _source: str
    _input_format: str | None
    _data: str
    _output_format: str
    _count: int
    _graph_uri: str | None = None
    _stored: bool = False

    def source(self) -> str:
        """Return the path of the imported file."""
        return self._source

    def input_format(self) -> str | None:
        """Return the detected or provided input format."""
        return self._input_format

    def data(self) -> str:
        """Return the imported RDF data."""
        return self._data

    def graph_uri(self) -> str | None:
        """Return the named graph URI used for the import."""
        return self._graph_uri

    def output_format(self) -> str:
        """Return the serialization format of the imported data."""
        return self._output_format

    def count(self) -> int:
        """Return the number of imported RDF triples."""
        return self._count

    def stored(self) -> bool:
        """Return whether the imported data was sent to a backend."""
        return self._stored


def import_file(input_file: str, input_format: str | None = None, backend: StorageBackend | None = None, graph_uri: str | None = None) -> ImportResult:
    """Parse an SPDX file, serialize it as Turtle, and load it into a backend."""
    path = Path(input_file)

    if not path.is_file():
        msg = f"File not found: {input_file}"
        raise FileNotFoundError(msg)

    if input_format is None:
        input_format = detect_format(path)

    # Create a graph for transforming data to turtle
    g = Graph()
    g.parse(path, format=input_format)
    ttl_data = g.serialize(format="turtle")

    stored = False

    if backend is not None:
        backend.load(data=ttl_data, data_format="turtle", graph_uri=graph_uri)
        stored = True

    return ImportResult(
        _source=input_file,
        _input_format=input_format,
        _data=ttl_data,
        _graph_uri=graph_uri,
        _output_format="turtle",
        _count=len(g),
        _stored=stored,
    )


def detect_format(path: Path) -> str:
    """Detect the RDF input format from the file extension."""
    suffixes = path.suffixes

    if path.suffix == ".jsonld" or suffixes[-2:] in [[".spdx", ".json"], [".spdx3", ".json"]]:
        return "json-ld"

    # Let's start only with json-ld firstly
    # if path.suffix in {".ttl", ".turtle"}:
    #     return "turtle"

    # if path.suffix == ".nt":
    #     return "nt"

    # if path.suffix in {".rdf", ".xml"}:
    #     return "xml"

    msg = f"Unsupported input format: {path.suffix}"
    raise ValueError(msg)
