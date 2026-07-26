# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from spdx_storage.backends.base import StorageBackend
from spdx_storage.backends.triplestorebackend import TriplestoreStorageBackend
from spdx_storage.importers.parser import ImportResult
from spdx_storage.importers.parser import import_file as parse_file


class SPDXStore:
    """Main interface for importing, storing, and exporting SPDX data."""

    def __init__(self, backend: StorageBackend | None = None) -> None:
        self.backend = backend

    @classmethod
    def connect(cls, backend: str, config: dict[str, Any]) -> SPDXStore:
        """Create an SPDXStore connected to a triplestore backend."""
        storage_backend = TriplestoreStorageBackend(backend, config)
        return cls(backend=storage_backend)

    def __enter__(self) -> SPDXStore:
        """Enter the store context."""
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Exit the store context and close the backend if possible."""
        self.close()

    def close(self) -> None:
        """Close the underlying backend if one exists."""
        if self.backend is not None:
            self.backend.close()

    def import_file(self, input_file: str, input_format: str | None = None, graph_uri: str | None = None) -> ImportResult:
        """Import an SPDX file and return information about the imported data."""
        return parse_file(input_file=input_file, input_format=input_format, backend=self.backend, graph_uri=graph_uri)

    # TODO: def export_file(self, input_file: str, export_format: str) -> ExportResult:
