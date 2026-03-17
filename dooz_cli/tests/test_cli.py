import pytest
from dooz_cli.cli import DoozCLI


def test_cli_initialization():
    cli = DoozCLI("ws://localhost:8765")
    assert cli.uri == "ws://localhost:8765"
