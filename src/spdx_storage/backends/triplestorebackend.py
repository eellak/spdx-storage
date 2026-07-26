# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from triplestore import Triplestore, TriplestoreBackend


class TriplestoreStorageBackend:
    """Storage backend that delegates RDF loading to the triplestore library."""

    def __init__(self, backend: str, config: dict[str, Any]) -> None:
        self.backend_name = backend
        self.config = config
        self.triplestore: TriplestoreBackend = Triplestore(backend, config)

    def load(self, data: str, data_format: str = "turtle", graph_uri: str | None = None) -> None:
        """Load RDF data into the configured triplestore backend."""
        suffix = self._suffix_for_format(data_format)

        if graph_uri is not None:
            self.config["graph"] = graph_uri

        with NamedTemporaryFile(mode="w", suffix=suffix, encoding="utf-8", delete=False) as temp_file:
            temp_file.write(data)
            temp_file_path = temp_file.name

        try:
            self.triplestore.load(temp_file_path)
        finally:
            Path(temp_file_path).unlink(missing_ok=True)

    def close(self) -> None:
        """Close the underlying backend if it exposes a close method."""
        close_method = getattr(self.triplestore, "close", None)

        if callable(close_method):
            close_method()

    def _suffix_for_format(self, data_format: str) -> str:
        """Return a file suffix supported by triplestore.load()."""
        if data_format == "turtle":
            return ".ttl"

        if data_format in {"nt", "n-triples"}:
            return ".nt"

        msg = f"Unsupported RDF format for triplestore loading: {data_format}"
        raise ValueError(msg)
