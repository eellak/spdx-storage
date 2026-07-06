from pathlib import Path

from rdflib import Graph

from spdx_storage.importers.parser import detect_format, import_file

EXAMPLE_FILE = Path("tests/example1.spdx3.json")


def test_detect_format_recognizes_json_ld():
    assert detect_format(EXAMPLE_FILE) == "json-ld"


def test_import_file_converts_spdx_json_ld_to_turtle():
    ttl_data = import_file(str(EXAMPLE_FILE))

    turtle_graph = Graph()
    turtle_graph.parse(data=ttl_data, format="turtle")

    source_graph = Graph()
    source_graph.parse(str(EXAMPLE_FILE), format="json-ld")

    assert len(turtle_graph) == len(source_graph)
    assert turtle_graph.isomorphic(source_graph)
