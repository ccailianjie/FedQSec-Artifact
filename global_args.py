"""Command-line options for the small workflow entry point."""

from __future__ import annotations

import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a FedQSec workflow round")
    parser.add_argument("--target", default="obu-1", help="Vehicle ID to protect")
    return parser.parse_args()
