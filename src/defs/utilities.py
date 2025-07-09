# Utility Functions
# Generated from piSeed045_piDefGC_utilities.pi
"""
Collection of utility functions for common string and data operations.
These functions are designed to be reusable across multiple projects.
Updated for testing syncCode functionality.
"""

import os
import sys
import json
from pathlib import Path
from json import loads, dumps
from datetime import datetime

DEFAULT_ENCODING = 'utf-8'
MAX_FILE_SIZE = 1024 * 1024  # 1MB
DEBUG_MODE = True  # New constant for testing

def clean_string(text: str) -> str:
    '''
    Clean and normalize a string by removing extra whitespace.

    Args:
        text: Input string to clean

    Returns:
        Cleaned string with normalized whitespace
    '''
    if not isinstance(text, str):
        print('clean_string', text)
        return str(text)
    return ' '.join(text.split())


def safe_json_load(file_path: str) -> dict:
    '''
    Safely load JSON from a file with error handling.

    Args:
        file_path: Path to the JSON file

    Returns:
        Dictionary from JSON file, or empty dict if error
    '''
    try:
        with open(file_path, 'r', encoding=DEFAULT_ENCODING) as f:
            return loads(f.read())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Error loading JSON from {file_path}: {e}')
        return {}


def timestamp_string() -> str:
    '''
    Generate a timestamp string for logging or file naming.

    Returns:
        ISO format timestamp string
    '''
    return datetime.now().isoformat()


def validate_email(email: str) -> bool:
    '''
    Simple email validation function.

    Args:
        email: Email address to validate

    Returns:
        True if email appears valid, False otherwise
    '''
    return '@' in email and '.' in email.split('@')[1]


if __name__ == '__main__':
    # Example usage
    test_string = '  Hello    World  '
    print(f'Cleaned: {clean_string(test_string)}')
    print(f'Timestamp: {timestamp_string()}')
    print(f'Debug mode: {DEBUG_MODE}')
    print(f'Email test: {validate_email("test@example.com")}')




