"""`import` command implementation for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# Copyright (c) 2026 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import ijson
import orjson
from rdflib import Graph
from triplestore import Triplestore

from .cmd_config import _resolve_config_path
from .config import ConfigManager

if TYPE_CHECKING:
    import argparse

JSON_OBJECT_BATCH_SIZE = 4_000
TRIPLE_BATCH_SIZE = 50_000


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

    # Initialize a triplestore instance
    config = ConfigManager(config_path)

    triplestore_config = {}
    for config_key in ("name", "graph", "conn_url", "auth"):
        value = config.get(config_key)
        if value is not None:
            triplestore_config[config_key] = value

    store = Triplestore(config.get("backend"), config=triplestore_config)

    # Read/parse the SPDX input file into RDF data and import the RDF data into the triplestore
    input_format = detect_format(input_path)
    try:
        _import_data(input_path, input_format, store)
    except (ValueError, OSError, ijson.JSONError, orjson.JSONEncodeError) as exc:
        msg = f"Failed to parse SPDX input file: {input_file}"
        raise ValueError(msg) from exc

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


def _import_data(input_path: Path, input_format: str, store: Triplestore) -> None:
    if input_format == "json-ld":
        do_import_in_batches(input_path, store)
        return

    data_graph = Graph()
    data_graph.parse(input_path, format=input_format)
    store.add_all(data_graph)


def do_import_in_batches(input_path: Path, store: Triplestore) -> None:
    # Read the document context without loading the whole file.
    with input_path.open("rb") as input_stream:
        contexts = ijson.items(input_stream, "@context", use_float=True)
        try:
            context = next(contexts)
        except StopIteration as exc:
            msg = f"Missing @context in JSON-LD input: {input_path}"
            raise ValueError(msg) from exc

    json_objects: list[object] = []
    triple_batch: list[tuple[object, object, object]] = []

    def process_json_objects() -> None:
        if not json_objects:
            return

        batch_graph = Graph()
        jsonld_fragment = {"@context": context, "@graph": json_objects}

        batch_graph.parse(data=orjson.dumps(jsonld_fragment), format="json-ld", publicID=input_path.resolve().as_uri())
        json_objects.clear()

        for triple in batch_graph:
            triple_batch.append(triple)
            if len(triple_batch) >= TRIPLE_BATCH_SIZE:
                store.add_all(triple_batch)
                triple_batch.clear()

    with input_path.open("rb") as input_stream:
        for json_object in ijson.items(input_stream, "@graph.item", use_float=True):
            json_objects.append(json_object)
            if len(json_objects) >= JSON_OBJECT_BATCH_SIZE:
                process_json_objects()

    # Parse the final JSON-object batch and import the final RDF batch
    process_json_objects()
    if triple_batch:
        store.add_all(triple_batch)
