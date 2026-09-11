"""Configuration file handling for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import tomllib
import warnings
from pathlib import Path
from typing import ClassVar

import platformdirs

DEFAULT_CONFIG_FILENAME = "config.toml"


def get_default_config_file() -> Path:
    config_dir = Path(platformdirs.user_config_path("spdx-storage", "spdx-storage"))
    return config_dir / DEFAULT_CONFIG_FILENAME


class ConfigManager:
    KNOWN_CONFIG_KEYS: ClassVar[set[str]] = {"auth", "backend", "conn_url", "graph", "name"}
    ALIASES: ClassVar[dict[str, str]] = {"conn_url": "base_url"}

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
        resolved_key = self._resolve_key(key)
        return self._data.get(resolved_key)

    def set(self, key: str, value: str) -> None:
        resolved_key = self._resolve_key(key)
        self._data[resolved_key] = value
        if key not in self.KNOWN_CONFIG_KEYS:
            warnings.warn(f"Unknown configuration key {key} will not be used.", stacklevel=2)

    def items(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._data.items()))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as config_file:
            for key, value in self._data.items():
                config_file.write(f"{key} = {json.dumps(value)}\n")

    def _resolve_key(self, key: str) -> str:
        return self._ALIASES.get(key, key)
