# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from rdflib import Graph

from spdx_storage import SPDXStore

TURTLE_DATA = """
@prefix ex: <http://example.org/> .

ex:package ex:name "hello" .
ex:package ex:license "GPL-3.0-or-later" .
ex:package ex:contains ex:file .
ex:file ex:name "hello.c" .
"""


def test_spdx_store_exports_rdf_data_to_json_ld(tmp_path):
    store = SPDXStore()

    output_file = tmp_path / "exported.spdx.json"

    result = store.export_file(data=TURTLE_DATA, output_file=str(output_file), output_format="json-ld")

    source_graph = Graph()
    source_graph.parse(data=TURTLE_DATA, format="turtle")

    assert output_file.exists()
    assert result.data() == TURTLE_DATA
    assert result.output_file() == str(output_file)
    assert result.input_format() == "turtle"
    assert result.output_format() == "json-ld"
    assert result.count() == len(source_graph)

    exported_graph = Graph()
    exported_graph.parse(str(output_file), format="json-ld")

    assert exported_graph.isomorphic(source_graph)
