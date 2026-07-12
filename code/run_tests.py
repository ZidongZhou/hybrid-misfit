from __future__ import annotations

import importlib.util
import argparse
import os
import sys
import unittest
from pathlib import Path


ROOT = Path(os.environ.get("SWAA_OUTPUTS_ROOT", Path(__file__).resolve().parents[1])).resolve()
TEST_DIR = ROOT / "tests"


def load_tests() -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.discover(str(TEST_DIR), pattern="test_*.py")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run package tests.")
    parser.add_argument("--outputs-root", default=None, help="Project root containing generated tables, figures, manuscript, and tests.")
    args = parser.parse_args()
    if args.outputs_root:
        os.environ["SWAA_OUTPUTS_ROOT"] = str(Path(args.outputs_root).expanduser().resolve())
        global ROOT, TEST_DIR
        ROOT = Path(os.environ["SWAA_OUTPUTS_ROOT"]).resolve()
        TEST_DIR = ROOT / "tests"
    if not TEST_DIR.exists():
        raise SystemExit(f"Test directory not found: {TEST_DIR}")
    suite = load_tests()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
