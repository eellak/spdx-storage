# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from rdflib import Graph

from spdx_storage import SPDXStore

EXAMPLE_FILE = Path("tests/example1.spdx3.json")


def test_spdx_store_import_file_returns_import_result():
    store = SPDXStore()

    result = store.import_file(str(EXAMPLE_FILE))

    assert result.source() == str(EXAMPLE_FILE)
    assert result.input_format() is None
    assert result.output_format() == "turtle"
    assert result.count() > 0
    assert result.graph() is None
    assert isinstance(result.data(), str)

    graph = Graph()
    graph.parse(data=result.data(), format="turtle")

    assert len(graph) == result.count()
