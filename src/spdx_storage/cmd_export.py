"""`export` command implementation for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def add_export_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("export", help="Export SPDX data from storage.")
    parser.add_argument("id", help="ID of the SPDX data to export.")
    parser.add_argument("--output", help="Output file path.")
    parser.add_argument("--only", help="Export only the specified item without connected data.")
    parser.add_argument("--format", default="json-ld", help="Output format for exported SPDX data.")
    parser.set_defaults(func=handle_export_command)


def do_export(
    entity_id: str,
    config_file: str | None = None,
    output: str | None = None,
    only: str | None = None,
    fmt: str | None = None,
) -> int:
    raised_err_msg = "The export command is not implemented yet."
    raise NotImplementedError(raised_err_msg)


def handle_export_command(args: argparse.Namespace) -> int:
    return do_export(
        args.id,
        getattr(args, "config_file", None),
        getattr(args, "output", None),
        getattr(args, "only", None),
        getattr(args, "format", None),
    )
