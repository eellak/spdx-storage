"""`config` command implementation for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse
import sys
from pathlib import Path

from .config import ConfigManager, get_default_config_file


def add_config_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("config", help="Manage configuration settings.")
    subcommands = parser.add_subparsers(dest="subcommand", required=True)

    set_parser = subcommands.add_parser("set", help="Set a configuration key.")
    set_parser.add_argument("key", help="Configuration key to set.")
    set_parser.add_argument("value", help="Value to set for the configuration key.")

    get_parser = subcommands.add_parser("get", help="Get a configuration key.")
    get_parser.add_argument("key", help="Configuration key to retrieve.")

    list_parser = subcommands.add_parser("list", help="List all configuration keys.")

    set_parser.set_defaults(func=handle_config_command)
    get_parser.set_defaults(func=handle_config_command)
    list_parser.set_defaults(func=handle_config_command)


def _resolve_config_path(config_file: str | None) -> Path:
    if config_file is not None:
        return Path(config_file)
    return get_default_config_file()


# ruff: disable[print]


def handle_config_command(args: argparse.Namespace) -> int:
    config_path = _resolve_config_path(getattr(args, "config_file", None))
    manager = ConfigManager(config_path)

    if args.subcommand == "set":
        manager.set(args.key, args.value)
        manager.save()
        return 0

    if args.subcommand == "get":
        value = manager.get(args.key)
        if value is None:
            print(f"error: configuration key '{args.key}' not found", file=sys.stderr)
            return 1
        print(value)
        return 0

    if args.subcommand == "list":
        for key, value in manager.items():
            print(f"{key} = {value}")
        return 0

    print("error: unsupported config subcommand", file=sys.stderr)
    return 1


# ruff: enable[print]
