"""Tests for the spdx-storage import command."""
# Copyright (c) 2026 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0
# ruff: file-ignore[assert]

from __future__ import annotations

import random
from pathlib import Path

import pytest
from rdflib import Graph
from triplestore import Triplestore

from spdx_storage.cmd_import import detect_format, do_import
from spdx_storage.config import ConfigManager

TEST_BACKEND = "oxigraph"
TEST_GRAPH = "https://example.org/spdx-test"


SUPPORTED_PATTERNS = (
    "*.jsonld",
    "*.spdx.json",
    "*.spdx3.json",
)


@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(f"""
backend = "{TEST_BACKEND}"
graph = "{TEST_GRAPH}"
""".strip(),
        encoding="utf-8")
    return path


@pytest.fixture
def input_file() -> Path:
    examples_dir = Path(__file__).parent / "spdx-examples"
    supported_files = [path for pattern in SUPPORTED_PATTERNS for path in examples_dir.rglob(pattern)]
    if not supported_files:
        pytest.fail(f"No supported SPDX files found in {examples_dir}")
    return random.choice(supported_files)


@pytest.fixture
def data_graph(input_file: Path) -> Graph:
    graph = Graph()
    graph.parse(input_file, format=detect_format(input_file))
    return graph


def test_import_missing_input_file(config_file: Path) -> None:
    missing_file = "missing.spdx3.json"
    with pytest.raises(
        FileNotFoundError,
        match="Input file does not exist or is not a file"):
        do_import(str(missing_file), str(config_file))


def test_import_input_path_is_directory(config_file: Path, tmp_path: Path) -> None:
    input_directory = tmp_path / "input.spdx3.json"
    input_directory.mkdir(exist_ok=True)
    with pytest.raises(
        FileNotFoundError,
        match="Input file does not exist or is not a file"):
        do_import(str(input_directory), str(config_file))


def test_import_missing_config_file(input_file: Path) -> None:
    missing_config = "missing.toml"
    with pytest.raises(
        FileNotFoundError,
        match="Configuration file does not exist or is not a file"):
        do_import(str(input_file), str(missing_config))


def test_import_config_path_is_directory(input_file: Path, tmp_path: Path) -> None:
    config_directory = tmp_path / "configuration.toml"
    config_directory.mkdir(exist_ok=True)
    with pytest.raises(
        FileNotFoundError,
        match="Configuration file does not exist or is not a file"):
        do_import(str(input_file), str(config_directory))


@pytest.mark.parametrize(("filename", "expected_format"),
    [
        ("example.jsonld", "json-ld"),
        ("example.spdx.json", "json-ld"),
        ("example.spdx3.json", "json-ld"),
    ],
)
def test_detect_format(filename: str, expected_format: str) -> None:
    assert detect_format(Path(filename)) == expected_format


def test_detect_format_unsupported() -> None:
    with pytest.raises(ValueError, match="Unsupported input format"):
        detect_format(Path("example.txt"))


def test_import_config_values(config_file: Path) -> None:
    manager = ConfigManager(config_file)
    assert manager.get("backend") == TEST_BACKEND
    assert manager.get("graph") == TEST_GRAPH


def test_import_into_triplestore(config_file: Path, input_file: Path) -> None:
    manager = ConfigManager(config_file)

    triplestore_config = {}
    for config_key, store_key in (
        ("name", "name"),
        ("graph", "graph"),
        ("conn_url", "base_url"),
        ("auth", "auth"),
    ):
        value = manager.get(config_key)
        if value is not None:
            triplestore_config[store_key] = value

    store = Triplestore(manager.get("backend"), config=triplestore_config)
    assert store.graph_uri == TEST_GRAPH

    input_format = detect_format(input_file)
    source_graph = Graph()
    source_graph.parse(input_file, format=input_format)

    store.clear()  # Ensure the triplestore is empty before import
    store.add_all(source_graph)

    # Verify that the number of imported triples matches the source graph
    count_result = store.query(
        f"""
        SELECT (COUNT(*) AS ?count)
        WHERE {{
            GRAPH <{TEST_GRAPH}> {{
                ?s ?p ?o .
            }}
        }}
        """
    )
    assert int(count_result[0]["count"]) == len(source_graph)

    # Verify that every source triple exists in the triplestore
    triple_patterns = "\n".join(
        f"{subject.n3()} {predicate.n3()} {obj.n3()} ."
        for subject, predicate, obj in source_graph
    )

    all_triples_exist = store.execute(
        f"""
        ASK {{
            GRAPH <{TEST_GRAPH}> {{
                {triple_patterns}
            }}
        }}
        """
    )
    assert all_triples_exist is True
