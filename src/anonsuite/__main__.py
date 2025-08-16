#!/usr/bin/env python3
"""
AnonSuite CLI Entry Point

This module provides the command-line interface entry point for AnonSuite.
It can be executed using: python -m anonsuite
"""

import sys

from .main import main

if __name__ == "__main__":
    sys.exit(main())
