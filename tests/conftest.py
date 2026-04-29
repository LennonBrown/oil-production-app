# tests/conftest.py
# This file is automatically loaded by pytest before running any tests.
# It adds the project root to the Python path so that
# 'from app import ...' works correctly inside tests.

import sys
import os

# Add the project root directory to the Python path
# This lets pytest find the 'app' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))