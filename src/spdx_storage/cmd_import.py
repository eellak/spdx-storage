"""`import` command implementation for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def add_import_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("import", help="Import SPDX data from a file.")
    parser.add_argument("input_file", help="Path to the SPDX input file.")
    parser.set_defaults(func=handle_import_command)


def do_import(input_file: str, config_file: str | None = None) -> int:
    raised_err_msg = "The import command is not implemented yet."
    raise NotImplementedError(raised_err_msg)


def handle_import_command(args: argparse.Namespace) -> int:
    return do_import(args.input_file, getattr(args, "config_file", None))
