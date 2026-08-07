"""Standalone entry point for PyInstaller (cli.py uses package-relative imports and can't be
run directly as a script)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client_updater.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
