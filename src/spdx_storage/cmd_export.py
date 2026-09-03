"""`export` command implementation for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras, Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from rdflib import BNode, Graph, URIRef
from triplestore import Triplestore

from .cmd_config import _resolve_config_path
from .config import ConfigManager

if TYPE_CHECKING:
    import argparse


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
    # Resolve and Validate configuration needed for storage from config file
    config_path = _resolve_config_path(config_file=config_file)
    if config_file is not None and not config_path.is_file():
        msg = f"Configuration file does not exist or is not a file: {config_file}"
        raise FileNotFoundError(msg)

    manager = ConfigManager(config_path)
    backend = manager.get("backend")
    name = manager.get("name")
    graph = manager.get("graph")
    conn_url = manager.get("conn_url")
    auth = manager.get("auth")

    # Initialize a triplestore instance and retrieve the RDF data
    triplestore_config = {}
    if name is not None:
        triplestore_config["name"] = name
    if graph is not None:
        triplestore_config["graph"] = graph
    if conn_url is not None:
        triplestore_config["base_url"] = conn_url
    if auth is not None:
        triplestore_config["auth"] = auth

    store = Triplestore(backend, config=triplestore_config)
    if graph is not None:
        sparql_query = f"""
            CONSTRUCT {{
                ?s ?p ?o .
            }}
            WHERE {{
                GRAPH <{graph}> {{
                    ?s ?p ?o .
                }}
            }}
        """
    else:
        sparql_query = """
            CONSTRUCT {
                ?s ?p ?o .
            }
            WHERE {
                ?s ?p ?o .
            }
        """
    results_ttl = store.execute(sparql_query)

    # Parse the retrieved RDF data into a graph
    full_graph = Graph()
    full_graph.parse(data=results_ttl, format="turtle")

    # Check if the specified entity_id exists in the retrieved RDF data
    start_node = URIRef(entity_id)
    if (not any(full_graph.triples((start_node, None, None)))
        and not any(full_graph.triples((None, None, start_node)))):
        msg = f"SPDX entity not found: {entity_id}"
        raise ValueError(msg)

    # Build the export graph based on the specified entity_id and the 'only' flag
    export_graph = build_export_graph(full_graph, start_node, only=only)

    # Serialize the export graph to the specified format
    output_format = fmt or "json-ld"
    serialized_data = export_graph.serialize(format=output_format)

    # Write the serialized data to the output file or print it to stdout
    if output is not None:
        Path(output).write_text(serialized_data, encoding="utf-8")
    else:
        print(serialized_data)

    return 0


def build_export_graph(full_graph: Graph, start_node: URIRef, *, only: bool = False) -> Graph:
    export_graph = Graph()

    for prefix, namespace in full_graph.namespaces():
        export_graph.bind(prefix, namespace)

    if only:
        # Direct outgoing edges
        for triple in full_graph.triples((start_node, None, None)):
            export_graph.add(triple)
        # Direct incoming edges
        for triple in full_graph.triples((None, None, start_node)):
            export_graph.add(triple)
        return export_graph

    queue = deque([start_node])
    visited = set()

    while queue:
        node = queue.popleft()

        if node in visited:
            continue

        visited.add(node)

        # Outgoing edges: node -> object
        for subject, predicate, obj in full_graph.triples((node, None, None)):
            export_graph.add((subject, predicate, obj))

            if is_expandable_node(full_graph, obj) and obj not in visited:
                queue.append(obj)

        # Incoming edges: subject -> node
        for subject, predicate, obj in full_graph.triples((None, None, node)):
            export_graph.add((subject, predicate, obj))

            if isinstance(subject, (URIRef, BNode)) and subject not in visited:
                queue.append(subject)

    return export_graph


def is_expandable_node(graph: Graph, node: object) -> bool:
    return (
        isinstance(node, (URIRef, BNode))
        and any(graph.triples((node, None, None)))
    )


def handle_export_command(args: argparse.Namespace) -> int:
    return do_export(
        args.id,
        getattr(args, "config_file", None),
        getattr(args, "output", None),
        only=getattr(args, "only", False),
        fmt=getattr(args, "format", None),
    )


# ruff: enable[print]
