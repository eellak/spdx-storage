# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from rdflib import Graph

from spdx_storage.exporters.serializer import export_file


@dataclass
class ExportResult:
    """Information about an exported SPDX document."""

    _data: str
    _output_file: str
    _input_format: str
    _output_format: str
    _count: int

    def data(self) -> str:
        """Return the RDF data that was exported."""
        return self._data

    def output_file(self) -> str:
        """Return the path of the exported file."""
        return self._output_file

    def input_format(self) -> str:
        """Return the input RDF format."""
        return self._input_format

    def output_format(self) -> str:
        """Return the output serialization format."""
        return self._output_format

    def count(self) -> int:
        """Return the number of exported RDF triples."""
        return self._count


class SPDXStore:
    """Main interface for importing, storing, and exporting SPDX data."""

    def export_file(self, data: str, output_file: str, input_format: str = "turtle", output_format: str = "json-ld") -> ExportResult:
        """Export RDF data to the requested output file."""
        output_path = export_file(data=data, output_file=output_file, input_format=input_format, output_format=output_format)

        graph = Graph()
        graph.parse(data=data, format=input_format)

        return ExportResult(
            _data=data,
            _output_file=str(output_path),
            _input_format=input_format,
            _output_format=output_format,
            _count=len(graph),
        )
