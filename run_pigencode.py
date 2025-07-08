#!/usr/bin/env python3
"""
Simple wrapper script to run piGenCode commands for testing
Usage: python run_pigencode.py genCode piDef 2
"""
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pigencode.main import main

if __name__ == "__main__":
    # Prepend 'piGenCode' to arguments
    sys.argv = ['piGenCode'] + sys.argv[1:]
    main()
