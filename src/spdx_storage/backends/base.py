# Copyright (C) 2025 Maira Papadopoulou
# SPDX-License-Identifier: Apache-2.0

from typing import Protocol


class StorageBackend(Protocol):
    """Interface for storage backends used by SPDXStore."""

    def load(self, data: str, data_format: str, graph_uri: str | None = None) -> None:
        """Load RDF data into the backend."""

    def close(self) -> None:
        """Close the backend if needed."""
