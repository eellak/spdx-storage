"""`export` command implementation for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# Copyright (c) 2026 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from rdflib import BNode, Graph, URIRef
from triplestore import Triplestore

from .cmd_config import _resolve_config_path
from .config import ConfigManager

if TYPE_CHECKING:
    import argparse


@dataclass(frozen=True)
class BlankStep:
    predicate: URIRef
    outgoing: bool


@dataclass(frozen=True)
class BlankPath:
    anchor: URIRef
    steps: tuple[BlankStep, ...]


def add_export_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("export", help="Export SPDX data from storage.")
    parser.add_argument("id", help="ID of the SPDX data to export.")
    parser.add_argument("--output", help="Output file path.")
    parser.add_argument("--only", action="store_true", help="Export only the specified item without connected data.")
    parser.add_argument("--format", default="json-ld", help="Output format for exported SPDX data.")
    parser.set_defaults(func=handle_export_command)


# ruff: disable[print]


def do_export(entity_id: str, config_file: str | None = None,
              output: str | None = None, *, only: bool = False, fmt: str | None = None) -> int:
    # Resolve and validate configuration file
    config_path = _resolve_config_path(config_file=config_file)
    if config_file is not None and not config_path.is_file():
        msg = f"Configuration file does not exist or is not a file: {config_file}"
        raise FileNotFoundError(msg)

    # Initialize a triplestore instance
    manager = ConfigManager(config_path)

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

    # Check if the specified entity_id exists in the retrieved RDF data
    start_node = URIRef(entity_id)
    start_graph = query_node_edges(store, start_node, include_incoming=True)
    if len(start_graph) == 0:
        msg = f"SPDX entity not found: {entity_id}"
        raise ValueError(msg)

    # Build the export graph based on the specified entity_id and the 'only' flag
    export_graph = start_graph if only else bfs_export_graph(store, start_node, start_graph)

    # Serialize the export graph to the specified format
    output_format = fmt or "json-ld"
    serialized_data = export_graph.serialize(format=output_format)

    # Write the serialized data to the output file or print it to stdout
    if output is not None:
        Path(output).write_text(serialized_data, encoding="utf-8")
    else:
        print(serialized_data)

    return 0


def bfs_export_graph(store: Triplestore, start_node: URIRef, start_graph: Graph) -> Graph:
    # First level: incoming + outgoing
    uri_frontier, blank_node_frontier = get_initial_frontiers(start_node, start_graph)

    visited_uris: set[URIRef] = {start_node}
    visited_blank_node_paths: set[BlankPath] = set()

    while uri_frontier or blank_node_frontier:
        # Expand URI nodes
        next_uri_frontier, next_blank_node_frontier = expand_uri_frontier(store, uri_frontier, visited_uris)

        # Expand blank-node paths
        blank_uris, nested_blank_paths = expand_blank_node_frontier(
            store, blank_node_frontier, visited_blank_node_paths)
        next_uri_frontier.update(blank_uris)
        next_blank_node_frontier.update(nested_blank_paths)

        uri_frontier = next_uri_frontier
        blank_node_frontier = next_blank_node_frontier

    return query_export_graph(store, start_node, visited_uris, visited_blank_node_paths)


def get_initial_frontiers(start_node: URIRef, start_graph: Graph) -> tuple[set[URIRef], set[BlankPath]]:
    uri_frontier: set[URIRef] = set()
    blank_node_frontier: set[BlankPath] = set()

    for subject, predicate, obj in start_graph:
        # Outgoing from start node
        if subject == start_node:
            next_node = obj
            outgoing = True
        # Incoming to start node
        elif obj == start_node:
            next_node = subject
            outgoing = False
        else:
            continue

        if isinstance(next_node, URIRef):
            uri_frontier.add(next_node)
        elif isinstance(next_node, BNode):
            blank_node_frontier.add(BlankPath(anchor=start_node, steps=(BlankStep(predicate, outgoing=outgoing),)))

    return uri_frontier, blank_node_frontier


def expand_uri_frontier(store: Triplestore, uri_frontier: set[URIRef],
                        visited_uris: set[URIRef]) -> tuple[set[URIRef], set[BlankPath]]:
    next_uri_frontier: set[URIRef] = set()
    next_blank_node_frontier: set[BlankPath] = set()

    for node in uri_frontier:
        if node in visited_uris:
            continue

        visited_uris.add(node)

        graph_result = query_node_edges(store, node)

        for _, predicate, obj in graph_result:
            if isinstance(obj, URIRef):
                next_uri_frontier.add(obj)

            elif isinstance(obj, BNode):
                next_blank_node_frontier.add(BlankPath(anchor=node, steps=(BlankStep(predicate, outgoing=True),)))

    return next_uri_frontier, next_blank_node_frontier


def expand_blank_node_frontier(store: Triplestore, blank_node_frontier: set[BlankPath],
                               visited_blank_node_paths: set[BlankPath]) -> tuple[set[URIRef], set[BlankPath]]:
    next_uri_frontier: set[URIRef] = set()
    next_blank_node_frontier: set[BlankPath] = set()

    for blank_node_path in blank_node_frontier:
        if blank_node_path in visited_blank_node_paths:
            continue

        visited_blank_node_paths.add(blank_node_path)

        graph_result = query_blank_node_edges(store, blank_node_path)

        for _, predicate, obj in graph_result:
            if isinstance(obj, URIRef):
                next_uri_frontier.add(obj)

            elif isinstance(obj, BNode):
                next_blank_node_frontier.add(
                    BlankPath(anchor=blank_node_path.anchor,
                              steps=(*blank_node_path.steps, BlankStep(predicate, outgoing=True))))

    return next_uri_frontier, next_blank_node_frontier


def query_node_edges(store: Triplestore, node: URIRef, *, include_incoming: bool = False) -> Graph:
    node = node.n3()

    edges_part = f"{{ {node} ?p ?o . }}"
    construct_part = f"{node} ?p ?o ."
    if include_incoming:
        edges_part += f" UNION {{ ?s ?p {node} . }}"
        construct_part += f"\n?s ?p {node} ."
    where_part = (f"GRAPH <{store.graph_uri}> {{ {edges_part} }}" if store.graph_uri is not None else edges_part)

    direct_edge_query = f"""
        CONSTRUCT {{
            {construct_part}
        }}
        WHERE {{ {where_part} }}"""
    results_ttl = store.execute(direct_edge_query)

    result_graph = Graph()
    result_graph.parse(data=results_ttl, format="turtle")
    return result_graph


def query_blank_node_edges(store: Triplestore, blank_node_path: BlankPath) -> Graph:
    path_pattern, current_node = build_blank_path_pattern(blank_node_path)

    edges_part = f"""
        {path_pattern}
        {current_node} ?p ?o .
    """
    where_part = (f"GRAPH <{store.graph_uri}> {{ {edges_part} }}" if store.graph_uri is not None else edges_part)

    query = f"""
        CONSTRUCT {{
            {current_node} ?p ?o .
        }}
        WHERE {{ {where_part} }}"""
    results_ttl = store.execute(query)

    result_graph = Graph()
    result_graph.parse(data=results_ttl, format="turtle")
    return result_graph


def build_blank_path_pattern(blank_path: BlankPath) -> tuple[str, str]:
    current = blank_path.anchor.n3()
    patterns = []

    for index, step in enumerate(blank_path.steps):
        next_node = f"?blank{index}"
        if step.outgoing:
            patterns.append(f"{current} {step.predicate.n3()} {next_node} .")
        else:
            patterns.append(f"{next_node} {step.predicate.n3()} {current} .")
        patterns.append(f"FILTER(isBlank({next_node}))")
        current = next_node
    return "\n".join(patterns), current


def query_export_graph(store: Triplestore, start_node: URIRef,
                       visited_uris: set[URIRef], visited_blank_paths: set[BlankPath]) -> Graph:
    # Outgoing edges from all discovered URI nodes
    uri_values = " ".join(node.n3() for node in visited_uris)

    # Incoming edges to the initial node
    branches = [
        f"""{{
            VALUES ?s {{ {uri_values} }}
            ?s ?p ?o .
        }}""",
        f"""{{
            VALUES ?o {{ {start_node.n3()} }}
            ?s ?p ?o .
        }}""",
    ]

    # Outgoing edges from all discovered blank nodes
    for blank_path in visited_blank_paths:
        path_pattern, current_node = build_blank_path_pattern(blank_path)

        branches.append(f"""{{
                {path_pattern}
                {current_node} ?p ?o .
                BIND({current_node} AS ?s)
            }}""")
    edges_part = "\nUNION\n".join(branches)
    where_part = (f"GRAPH <{store.graph_uri}> {{ {edges_part} }}" if store.graph_uri is not None else edges_part)

    query = f"""
        CONSTRUCT {{
            ?s ?p ?o .
        }}
        WHERE {{ {where_part} }}"""

    results_ttl = store.execute(query)

    export_graph = Graph()
    export_graph.parse(data=results_ttl, format="turtle")
    return export_graph


def handle_export_command(args: argparse.Namespace) -> int:
    return do_export(
        args.id,
        getattr(args, "config_file", None),
        getattr(args, "output", None),
        only=getattr(args, "only", False),
        fmt=getattr(args, "format", None),
    )


# ruff: enable[print]
