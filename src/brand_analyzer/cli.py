#!/usr/bin/env python3
"""
Brand Analyzer CLI Module
"""

import sys
from pathlib import Path

# Add the src directory to Python path (where main.py is now located)
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

# Import the CLI from main.py
from main import cli

if __name__ == "__main__":
    cli()
