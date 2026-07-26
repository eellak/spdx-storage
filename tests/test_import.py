# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from rdflib import Graph

from spdx_storage import SPDXStore
from spdx_storage.importers.parser import detect_format, import_file

EXAMPLE_FILE = Path("tests/example1.spdx3.json")
GRAPH_URI = "urn:spdx-storage:test:example1"


def test_detect_format_recognizes_json_ld():
    assert detect_format(EXAMPLE_FILE) == "json-ld"


def test_import_file_converts_spdx_json_ld_to_turtle():
    result = import_file(str(EXAMPLE_FILE))
    ttl_data = result.data()

    turtle_graph = Graph()
    turtle_graph.parse(data=ttl_data, format="turtle")

    source_graph = Graph()
    source_graph.parse(str(EXAMPLE_FILE), format="json-ld")

    assert len(turtle_graph) == len(source_graph)
    assert turtle_graph.isomorphic(source_graph)


def test_spdx_store_imports_file_into_oxigraph_backend():
    config = {"graph": GRAPH_URI}

    with SPDXStore.connect("oxigraph", config) as store:
        result = store.import_file(str(EXAMPLE_FILE))

        results = store.backend.triplestore.query(
            f"""
            SELECT ?s ?p ?o
            WHERE {{
                GRAPH <{GRAPH_URI}> {{
                    ?s ?p ?o .
                }}
            }}
            """,
        )

    assert result.source() == str(EXAMPLE_FILE)
    assert result.output_format() == "turtle"
    assert result.count() > 0
    assert result.stored() is True
    assert len(results) == result.count()


def test_spdx_store_imports_file_into_graphdb_backend():
    config = {
        "name": "spdx-test",
        "graph": GRAPH_URI,
    }

    with SPDXStore.connect("graphdb", config) as store:
        store.backend.triplestore.clear()

        result = store.import_file(str(EXAMPLE_FILE))

        results = store.backend.triplestore.query(
            f"""
            SELECT ?s ?p ?o
            WHERE {{
                GRAPH <{GRAPH_URI}> {{
                    ?s ?p ?o .
                }}
            }}
            """,
        )

    assert result.source() == str(EXAMPLE_FILE)
    assert result.output_format() == "turtle"
    assert result.count() > 0
    assert result.stored() is True
    assert len(results) == result.count()
