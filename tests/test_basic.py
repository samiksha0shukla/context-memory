# This is a basic test. I intended to show the pattern on how to start unit testing. This contains only testing initialization and non-existent memory. 
# TODO: If you want, I can help with setting up unit tests further. The folder 'tests' is designed for it. 

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from src.contextmemory.memory.memory import ContextMemory

def test_memory_init():
    """This tests that ContextMemory can be initialized."""
    mock_db = Mock(spec=Session)
    memory = ContextMemory(mock_db)
    assert memory.db == mock_db


def test_updating_non_existent_memory():
    """This tests updating memory that doesn't exist. If it doesn't it returns a 'None' value. """
    mock_db = Mock(spec=Session)
    mock_db.get.return_value = None
    
    memory = ContextMemory(mock_db)
    
    with pytest.raises(ValueError, match="Memory with 999 not found"):
        memory.update(memory_id=999, text="New text")


if __name__ == "__main__":
    try:
        test_memory_init()
        test_updating_non_existent_memory()
        print("Basic tests passed")
    except Exception as e:
        print(f"Test failed: {e}")
        raise
