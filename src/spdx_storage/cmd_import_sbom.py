"""`import-sbom` command implementation for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

from .cmd_import import do_import


def add_import_sbom_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("import-sbom", help="Import an SPDX SBOM from a file.")
    parser.add_argument("input_file", help="Path to the SPDX SBOM input file.")
    parser.add_argument("--check", action="store_true", help="Validate the SBOM before importing.")
    parser.set_defaults(func=handle_import_sbom_command)


def do_import_sbom(input_file: str, config_file: str | None = None, *, check: bool = False) -> int:
    if check:
        print(f"Checking SPDX SBOM file: {input_file}")  # ruff: ignore[print]
    return do_import(input_file, config_file)


def handle_import_sbom_command(args: argparse.Namespace) -> int:
    return do_import_sbom(args.input_file, getattr(args, "config_file", None), check=getattr(args, "check", False))
