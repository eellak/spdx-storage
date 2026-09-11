"""`import` command implementation for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# Copyright (c) 2026 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rdflib import Graph
from triplestore import Triplestore

from .cmd_config import _resolve_config_path
from .config import ConfigManager

if TYPE_CHECKING:
    import argparse


def add_import_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("import", help="Import SPDX data from a file.")
    parser.add_argument("input_file", help="Path to the SPDX input file.")
    parser.set_defaults(func=handle_import_command)


def do_import(input_file: str, config_file: str | None = None) -> int:
    # Validate input file
    input_path = Path(input_file)
    if not input_path.is_file():
        msg = f"Input file does not exist or is not a file: {input_file}"
        raise FileNotFoundError(msg)

    # Resolve and validate configuration file
    config_path = _resolve_config_path(config_file=config_file)
    if config_file is not None and not config_path.is_file():
        msg = f"Configuration file does not exist or is not a file: {config_file}"
        raise FileNotFoundError(msg)

    # Read/parse the SPDX input file into RDF data
    input_format = detect_format(input_path)
    data_graph = Graph()
    try:
        data_graph.parse(input_path, format=input_format)
    except (ValueError, OSError) as exc:
        msg = f"Failed to parse SPDX input file: {input_file}"
        raise ValueError(msg) from exc

    # Initialize a triplestore instance and import the RDF data
    config = ConfigManager(config_path)

    triplestore_config = {}
    for config_key in ("name", "graph", "conn_url", "auth"):
        value = config.get(config_key)
        if value is not None:
            triplestore_config[config_key] = value

    store = Triplestore(config.get("backend"), config=triplestore_config)
    store.add_all(data_graph)

    return 0


def handle_import_command(args: argparse.Namespace) -> int:
    return do_import(args.input_file, getattr(args, "config_file", None))


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in {".json", ".jsonld", ".json-ld"}:
        return "json-ld"

    if suffix in {".ttl", ".turtle"}:
        return "turtle"

    if suffix == ".nt":
        return "nt"

    if suffix in {".rdf", ".xml"}:
        return "xml"

    msg = f"Unsupported input format: {path.suffix}"
    raise ValueError(msg)
