"""Configuration file handling for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import platformdirs

DEFAULT_CONFIG_FILENAME = "config.toml"

ALLOWED_CONFIG_KEYS = {
    "backend",
    "name",
    "graph",
    "conn_url",
    "auth",
}


def get_default_config_file() -> Path:
    config_dir = Path(platformdirs.user_config_path("spdx-storage", "spdx-storage"))
    return config_dir / DEFAULT_CONFIG_FILENAME


class ConfigManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else get_default_config_file()
        self._data: dict[str, str] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return

        with self.path.open("rb") as config_file:
            raw_data = tomllib.load(config_file)

        self._data = {str(key): str(value) for key, value in raw_data.items()}

    def get(self, key: str) -> str | None:
        if key in ALLOWED_CONFIG_KEYS:
            return self._data.get(key)
        msg = (
            f"Invalid configuration key: {key}\n"
            "Available configuration keys are:\n"
            "backend: Specifies the backend to be used for storage (e.g., sqlite, postgresql, etc.).\n"
            "name: Specifies the name of the repository/dataset.\n"
            "graph: Specifies the name of the graph inside the database.\n"
            "conn_url: Specifies the URL of the database connection.\n"
            "auth: Specifies the authentication payload to be used for the database connection."
        )
        raise ValueError(msg)

    def set(self, key: str, value: str) -> None:
        if key in ALLOWED_CONFIG_KEYS:
            self._data[key] = value
        else:
            msg = (
                f"Invalid configuration key: {key}\n"
                "Available configuration keys are:\n"
                "backend: Specifies the backend to be used for storage (e.g., sqlite, postgresql, etc.).\n"
                "name: Specifies the name of the repository/dataset.\n"
                "graph: Specifies the name of the graph inside the database.\n"
                "conn_url: Specifies the URL of the database connection.\n"
                "auth: Specifies the authentication payload to be used for the database connection."
            )
            raise ValueError(msg)

    def items(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._data.items()))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as config_file:
            for key, value in self._data.items():
                config_file.write(f"{key} = {json.dumps(value)}\n")
