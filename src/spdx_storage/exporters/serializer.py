# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from rdflib import Graph


def export_file(data: str, output_file: str, input_format: str, output_format: str = "json-ld") -> Path:
    """Serialize RDF data to the requested output format."""
    g = Graph()
    g.parse(data=data, format=input_format)

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    serialized_data = g.serialize(format=output_format)

    output_path.write_text(serialized_data, encoding="utf-8")

    return output_path
