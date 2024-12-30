import os

FIXTURES_DIR = os.path.dirname(os.path.abspath(__file__))

def get_fixture_path(filename: str) -> str:
    """Get the full path to a fixture file"""
    return os.path.join(FIXTURES_DIR, filename)
