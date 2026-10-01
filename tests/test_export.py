"""Tests for the spdx-storage export command."""
# Copyright (c) 2026 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0
# ruff: file-ignore[assert]

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.compare import isomorphic

from spdx_storage import cmd_export
from spdx_storage.cmd_export import (
    BlankPath,
    BlankStep,
    bfs_export_graph,
    build_blank_path_pattern,
    do_export,
    expand_blank_node_frontier,
    expand_uri_frontier,
    get_initial_frontiers,
    query_export_graph,
    query_node_edges,
)

START = URIRef("https://example.org/start")
NODE_A = URIRef("https://example.org/a")
NODE_B = URIRef("https://example.org/b")
NODE_C = URIRef("https://example.org/c")

P_OUT = URIRef("https://example.org/out")
P_IN = URIRef("https://example.org/in")
P_BLANK = URIRef("https://example.org/blank")
P_NESTED = URIRef("https://example.org/nested")

B_NODE_A = BNode("a")
B_NODE_B = BNode("b")


class RDFLibTestStore:
    """Small in-memory store used to execute export SPARQL queries in tests."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph
        self.graph_uri = None

    def execute(self, query: str) -> str:
        result = self.graph.query(query)
        return result.graph.serialize(format="turtle")


def test_blank_step_and_blank_path() -> None:
    step = BlankStep(predicate=P_BLANK, outgoing=True)
    path = BlankPath(anchor=START, steps=(step,))

    assert step.predicate == P_BLANK
    assert step.outgoing is True
    assert path.anchor == START
    assert path.steps == (step,)
    # BlankPath is structural and hashable
    same_path = BlankPath(anchor=START, steps=(BlankStep(P_BLANK, outgoing=True),))
    assert path == same_path
    assert len({path, same_path}) == 1


def test_build_blank_path_pattern() -> None:
    graph = Graph()
    blank0 = BNode("blank0")
    blank1 = BNode("blank1")
    wrong_blank = BNode("wrong")

    graph.add((blank0, P_IN, START))
    graph.add((blank0, P_NESTED, blank1))
    graph.add((blank1, P_OUT, NODE_A))
    # Unrelated blank node that must not be returned
    graph.add((wrong_blank, P_OUT, NODE_B))

    path = BlankPath(anchor=START, steps=(
        BlankStep(P_IN, outgoing=False), BlankStep(P_NESTED, outgoing=True)))
    pattern, current_node = build_blank_path_pattern(path)

    assert f"?blank0 {P_IN.n3()} {START.n3()} ." in pattern
    assert "FILTER(isBlank(?blank0))" in pattern
    assert f"?blank0 {P_NESTED.n3()} ?blank1 ." in pattern
    assert "FILTER(isBlank(?blank1))" in pattern
    assert current_node == "?blank1"

    query = f"""
        SELECT {current_node}
        WHERE {{
            {pattern}
        }}
    """
    results = list(graph.query(query))
    assert len(results) == 1
    assert results[0][0] == blank1


def test_get_initial_frontiers() -> None:
    graph = Graph()

    # Outgoing URI
    graph.add((START, P_OUT, NODE_A))
    # Incoming URI
    graph.add((NODE_B, P_IN, START))
    # Outgoing blank node
    graph.add((START, P_BLANK, B_NODE_A))
    # Incoming blank node
    graph.add((B_NODE_B, P_IN, START))
    # Literal must not become part of the BFS frontier
    graph.add((START, P_OUT, Literal("value")))
    # Irrelevant triple must not become part of the BFS frontier
    graph.add((NODE_C, P_OUT, Literal("value")))

    uri_frontier, blank_frontier = get_initial_frontiers(START, graph)

    assert uri_frontier == {NODE_A, NODE_B}
    assert blank_frontier == {
        BlankPath(anchor=START, steps=(BlankStep(P_BLANK, outgoing=True),)),
        BlankPath(anchor=START, steps=(BlankStep(P_IN, outgoing=False),)),
    }


def test_expand_uri_frontier(monkeypatch: pytest.MonkeyPatch) -> None:
    already_visited = NODE_B

    result_graph = Graph()
    result_graph.add((NODE_A, P_OUT, NODE_C))
    result_graph.add((NODE_A, P_BLANK, B_NODE_A))
    result_graph.add((NODE_A, P_OUT, Literal("ignored")))

    def fake_query_uri_frontier_edges(_store: object, nodes: set[URIRef]) -> Graph:
        assert nodes == {NODE_A}
        return result_graph

    monkeypatch.setattr(cmd_export, "query_uri_frontier_edges", fake_query_uri_frontier_edges)
    visited = {already_visited}
    uri_frontier, blank_frontier = expand_uri_frontier(object(), {NODE_A, already_visited}, visited)

    assert visited == {NODE_A, already_visited}
    assert uri_frontier == {NODE_C}
    assert blank_frontier == {BlankPath(anchor=NODE_A, steps=(BlankStep(P_BLANK, outgoing=True),))}


def test_expand_blank_node_frontier(monkeypatch: pytest.MonkeyPatch) -> None:
    initial_path = BlankPath(
        anchor=START,
        steps=(BlankStep(P_BLANK, outgoing=True),),
    )
    current_blank = BNode("current")
    nested_blank = BNode("nested")

    result_graph = Graph()
    result_graph.add((current_blank, P_OUT, NODE_A))
    result_graph.add((current_blank, P_NESTED, nested_blank))
    result_graph.add((current_blank, P_OUT, Literal("ignored")))

    def fake_query_blank_node_edges(_store: object, path: BlankPath) -> Graph:
        assert path == initial_path
        return result_graph

    monkeypatch.setattr(cmd_export, "query_blank_node_edges", fake_query_blank_node_edges)
    visited: set[BlankPath] = set()
    uri_frontier, blank_frontier = expand_blank_node_frontier(object(), {initial_path}, visited)

    assert visited == {initial_path}
    assert uri_frontier == {NODE_A}
    assert blank_frontier == {
        BlankPath(
            anchor=START,
            steps=(
                BlankStep(P_BLANK, outgoing=True),
                BlankStep(P_NESTED, outgoing=True)))
    }


def test_bfs_export_graph() -> None:
    graph = Graph()

    # First level:
    graph.add((URIRef("https://example.org/incoming"), P_IN, START))
    graph.add((START, P_OUT, NODE_A))
    graph.add((START, P_BLANK, B_NODE_A))

    # URI branch:
    # The last edge creates a cycle.
    graph.add((NODE_A, P_OUT, NODE_C))
    graph.add((NODE_C, P_OUT, NODE_A))

    # Blank-node branch:
    graph.add((B_NODE_A, P_OUT, NODE_B))
    graph.add((B_NODE_A, P_NESTED, B_NODE_B))
    graph.add((B_NODE_B, P_OUT, URIRef("https://example.org/e")))

    store = RDFLibTestStore(graph)
    # first retrieve incoming + outgoing edges of START.
    start_graph = query_node_edges(store, START, include_incoming=True)
    result = bfs_export_graph(store, START, start_graph)

    assert isomorphic(result, graph)


def test_query_node_edges_returns_only_outgoing_edges() -> None:
    graph = Graph()

    graph.add((START, P_OUT, NODE_A))
    graph.add((START, P_OUT, Literal("value")))
    # Incoming edge: should NOT be returned.
    graph.add((NODE_B, P_IN, START))
    # Completely unrelated.
    graph.add((NODE_B, P_OUT, NODE_C))

    store = RDFLibTestStore(graph)
    result = query_node_edges(store, START, include_incoming=False)

    expected = Graph()
    expected.add((START, P_OUT, NODE_A))
    expected.add((START, P_OUT, Literal("value")))

    assert isomorphic(result, expected)


def test_query_node_edges_includes_incoming_edges() -> None:
    graph = Graph()

    graph.add((START, P_OUT, NODE_A))
    graph.add((NODE_B, P_IN, START))
    # Unrelated edge.
    graph.add((NODE_B, P_OUT, NODE_C))

    store = RDFLibTestStore(graph)
    result = query_node_edges(store, START, include_incoming=True)

    expected = Graph()
    expected.add((START, P_OUT, NODE_A))
    expected.add((NODE_B, P_IN, START))

    assert isomorphic(result, expected)


def test_query_node_edges_includes_blank_node_edges() -> None:
    graph = Graph()

    graph.add((NODE_C, P_IN, START))
    graph.add((START, P_OUT, NODE_A))
    graph.add((START, P_BLANK, B_NODE_A))
    graph.add((B_NODE_A, P_OUT, NODE_B))
    graph.add((NODE_B, P_OUT, NODE_C))

    store = RDFLibTestStore(graph)
    result = query_node_edges(store, START, include_incoming=False)

    expected = Graph()
    expected.add((START, P_OUT, NODE_A))
    expected.add((START, P_BLANK, B_NODE_A))

    assert isomorphic(result, expected)


def test_query_node_edges_includes_blank_node_edges_with_incoming() -> None:
    graph = Graph()

    graph.add((NODE_C, P_IN, START))
    graph.add((START, P_OUT, NODE_A))
    graph.add((START, P_BLANK, B_NODE_A))
    graph.add((B_NODE_A, P_OUT, NODE_B))
    graph.add((NODE_B, P_OUT, NODE_C))

    store = RDFLibTestStore(graph)
    result = query_node_edges(store, START, include_incoming=True)

    expected = Graph()
    expected.add((NODE_C, P_IN, START))
    expected.add((START, P_OUT, NODE_A))
    expected.add((START, P_BLANK, B_NODE_A))

    assert isomorphic(result, expected)


def test_query_node_edges_not_includes_start_node() -> None:
    graph = Graph()

    graph.add((NODE_A, P_OUT, NODE_B))
    graph.add((NODE_A, P_BLANK, B_NODE_A))
    graph.add((B_NODE_A, P_OUT, NODE_B))
    graph.add((NODE_C, P_IN, B_NODE_A))

    store = RDFLibTestStore(graph)
    result = query_node_edges(store, START, include_incoming=True)

    assert len(result) == 0


def test_query_export_graph() -> None:
    graph = Graph()

    incoming = URIRef("https://example.org/incoming")
    unvisited_uri = URIRef("https://example.org/unvisited")
    nested_blank = BNode("nested")
    unrelated_blank = BNode("unrelated")
    p_deep = URIRef("https://example.org/deep")

    # Outgoing edges from visited URI nodes
    graph.add((START, P_OUT, NODE_A))
    graph.add((START, P_BLANK, B_NODE_A))
    graph.add((NODE_A, P_OUT, NODE_B))
    # Incoming edge to START -> must be included
    graph.add((incoming, P_IN, START))
    # Incoming edge to another visited URI -> must NOT be included
    graph.add((NODE_C, P_IN, NODE_A))
    # Outgoing edges from a visited blank node
    graph.add((B_NODE_A, P_OUT, NODE_C))
    graph.add((B_NODE_A, P_NESTED, nested_blank))
    # Outgoing edge from nested blank node.
    # It must NOT be included because its BlankPath is not visited.
    graph.add((nested_blank, p_deep, NODE_A))
    # Completely unvisited URI
    graph.add((unvisited_uri, P_OUT, NODE_C))
    # Completely unrelated blank node
    graph.add((unrelated_blank, P_OUT, NODE_B))

    store = RDFLibTestStore(graph)

    visited_uris = {START, NODE_A}

    visited_blank_paths = {
        BlankPath(
            anchor=START,
            steps=(BlankStep(P_BLANK, outgoing=True),))
    }

    result = query_export_graph(store, START, visited_uris, visited_blank_paths)

    expected = Graph()
    # Outgoing edges from visited URI nodes
    expected.add((START, P_OUT, NODE_A))
    expected.add((START, P_BLANK, B_NODE_A))
    expected.add((NODE_A, P_OUT, NODE_B))
    # Incoming edges only to START
    expected.add((incoming, P_IN, START))
    # Outgoing edges from visited blank node
    expected.add((B_NODE_A, P_OUT, NODE_C))
    expected.add((B_NODE_A, P_NESTED, nested_blank))

    assert isomorphic(result, expected)

    # These must not be part of the export.
    assert (NODE_C, P_IN, NODE_A) not in result
    assert (unvisited_uri, P_OUT, NODE_C) not in result
    assert (None, p_deep, NODE_A) not in result


def test_bfs_export_graph_handles_uri_cycle() -> None:
    graph = Graph()

    # START -> A -> B -> A
    graph.add((START, P_OUT, NODE_A))
    graph.add((NODE_A, P_OUT, NODE_B))
    graph.add((NODE_B, P_OUT, NODE_A))

    store = RDFLibTestStore(graph)
    start_graph = query_node_edges(store, START, include_incoming=True)
    result = bfs_export_graph(store, START, start_graph)

    assert isomorphic(result, graph)


def test_bfs_export_graph_expands_three_nested_blank_nodes() -> None:
    graph = Graph()

    blank1 = BNode("blank1")
    blank2 = BNode("blank2")
    blank3 = BNode("blank3")

    graph.add((START, P_BLANK, blank1))
    graph.add((blank1, P_NESTED, blank2))
    graph.add((blank2, P_NESTED, blank3))
    graph.add((blank3, P_OUT, Literal("final value")))

    store = RDFLibTestStore(graph)
    start_graph = query_node_edges(store, START, include_incoming=True)
    result = bfs_export_graph(store, START, start_graph)

    assert isomorphic(result, graph)
    assert (None, P_OUT, Literal("final value")) in result


class FakeConfigManager:
    def __init__(self, _path: Path) -> None:
        pass

    @staticmethod
    def get(key: str) -> str | None:
        values = {"backend": "fake", "name": None, "graph": None, "conn_url": None, "auth": None}
        return values[key]


@pytest.mark.parametrize(
    ("fmt", "suffix"),
    [
        ("json-ld", ".jsonld"),
        ("turtle", ".ttl"),
        ("nt", ".nt"),
    ],
)
def test_export_output_formats(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fmt: str, suffix: str) -> None:
    graph = Graph()
    graph.add((START, P_OUT, NODE_A))
    graph.add((START, P_OUT, Literal("value")))

    store = RDFLibTestStore(graph)

    monkeypatch.setattr(cmd_export, "ConfigManager", FakeConfigManager)
    monkeypatch.setattr(cmd_export, "Triplestore", lambda *_args, **_kwargs: store)

    output_file = tmp_path / f"export{suffix}"
    result = do_export(str(START), output=str(output_file), only=True, fmt=fmt)

    assert result == 0
    assert output_file.exists()
    assert output_file.stat().st_size > 0

    exported = Graph()
    exported.parse(output_file, format=fmt)

    assert isomorphic(exported, graph)


def test_do_export_raises_when_entity_does_not_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    store = RDFLibTestStore(Graph())

    monkeypatch.setattr(cmd_export, "ConfigManager", FakeConfigManager)
    monkeypatch.setattr(cmd_export, "Triplestore", lambda *_args, **_kwargs: store)

    with pytest.raises(ValueError, match=f"SPDX entity not found: {START}"):
        do_export(str(START))


def test_do_export_only_true_skips_bfs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    graph = Graph()

    graph.add((START, P_OUT, NODE_A))
    graph.add((NODE_A, P_OUT, NODE_B))

    store = RDFLibTestStore(graph)

    monkeypatch.setattr(cmd_export, "ConfigManager", FakeConfigManager)
    monkeypatch.setattr(cmd_export, "Triplestore", lambda *_args, **_kwargs: store)

    def fail_if_called(*_args: object, **_kwargs: object) -> Graph:
        pytest.fail("bfs_export_graph must not be called when only=True")
    monkeypatch.setattr(cmd_export, "bfs_export_graph", fail_if_called)

    output_file = tmp_path / "only.ttl"
    result = do_export(str(START), output=str(output_file), only=True, fmt="turtle")

    assert result == 0

    exported = Graph()
    exported.parse(output_file, format="turtle")

    expected = Graph()
    expected.add((START, P_OUT, NODE_A))

    assert isomorphic(exported, expected)


def test_do_export_only_false_runs_bfs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    graph = Graph()
    graph.add((START, P_OUT, NODE_A))

    store = RDFLibTestStore(graph)

    monkeypatch.setattr(cmd_export, "ConfigManager", FakeConfigManager)
    monkeypatch.setattr(cmd_export, "Triplestore", lambda *_args, **_kwargs: store)

    bfs_called = False

    bfs_result = Graph()
    bfs_result.add((START, P_OUT, NODE_A))
    bfs_result.add((NODE_A, P_OUT, NODE_B))

    def fake_bfs_export_graph(received_store: object, start_node: URIRef, start_graph: Graph) -> Graph:
        nonlocal bfs_called
        bfs_called = True

        assert received_store is store
        assert start_node == START
        assert (START, P_OUT, NODE_A) in start_graph

        return bfs_result

    monkeypatch.setattr(cmd_export, "bfs_export_graph", fake_bfs_export_graph)

    output_file = tmp_path / "full.ttl"
    result = do_export(str(START), output=str(output_file), only=False, fmt="turtle")

    assert result == 0
    assert bfs_called is True

    exported = Graph()
    exported.parse(output_file, format="turtle")

    assert isomorphic(exported, bfs_result)


def test_do_export_uses_jsonld_as_default_format(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    graph = Graph()
    graph.add((START, P_OUT, NODE_A))

    store = RDFLibTestStore(graph)

    monkeypatch.setattr(cmd_export, "ConfigManager", FakeConfigManager)
    monkeypatch.setattr(cmd_export, "Triplestore", lambda *_args, **_kwargs: store)

    output_file = tmp_path / "export.jsonld"
    result = do_export(str(START), output=str(output_file), only=True, fmt=None)

    assert result == 0
    assert output_file.exists()

    exported = Graph()
    exported.parse(output_file, format="json-ld")

    assert isomorphic(exported, graph)


def test_do_export_prints_to_stdout_when_output_is_none(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    graph = Graph()
    graph.add((START, P_OUT, NODE_A))

    store = RDFLibTestStore(graph)

    monkeypatch.setattr(cmd_export, "ConfigManager", FakeConfigManager)
    monkeypatch.setattr(cmd_export, "Triplestore", lambda *_args, **_kwargs: store)

    result = do_export(str(START), output=None, only=True, fmt="turtle")

    assert result == 0

    captured = capsys.readouterr()

    exported = Graph()
    exported.parse(data=captured.out, format="turtle")

    assert isomorphic(exported, graph)
