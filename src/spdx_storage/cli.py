"""Command-line interface for spdx-storage."""
# Copyright (c) 2026 Alexios Zavras
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import argparse
import sys

from .cmd_config import add_config_parser
from .cmd_export import add_export_parser
from .cmd_import import add_import_parser
from .cmd_import_sbom import add_import_sbom_parser


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="spdx-storage", description="SPDX storage command-line utility.")
    parser.add_argument("--config-file", help="Path to the configuration file.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    add_config_parser(subparsers)
    add_import_parser(subparsers)
    add_import_sbom_parser(subparsers)
    add_export_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help(sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
