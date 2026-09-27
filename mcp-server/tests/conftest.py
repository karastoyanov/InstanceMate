import pytest
from app import create_server


@pytest.fixture
def mcp():
    return create_server()
