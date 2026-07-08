# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from rdflib import Graph

from spdx_storage.importers.parser import import_file


@dataclass
class ImportResult:
    """Information about an imported SPDX document."""

    _source: str
    _input_format: str | None
    _data: str
    _output_format: str
    _count: int
    _graph_uri: str | None = None

    def source(self) -> str:
        """Return the path of the imported file."""
        return self._source

    def input_format(self) -> str | None:
        """Return the detected or provided input format."""
        return self._input_format

    def data(self) -> str:
        """Return the imported RDF data."""
        return self._data

    def graph(self) -> str | None:
        """Return the named graph URI used for the import."""
        return self._graph_uri

    def output_format(self) -> str:
        """Return the serialization format of the imported data."""
        return self._output_format

    def count(self) -> int:
        """Return the number of imported RDF triples."""
        return self._count


class SPDXStore:
    """Main interface for importing, storing, and exporting SPDX data."""

    def import_file(self, input_file: str, input_format: str | None = None, graph_uri: str | None = None) -> ImportResult:
        """Import an SPDX file and return information about the imported data."""
        ttl_data = import_file(input_file, input_format=input_format)

        graph = Graph()
        graph.parse(data=ttl_data, format="turtle")

        return ImportResult(
            _source=input_file,
            _input_format=input_format,
            _data=ttl_data,
            _graph_uri=graph_uri,
            _output_format="turtle",
            _count=len(graph),
        )

    # TODO: def export_file(self, input_file: str, export_format: str) -> ExportResult:
