import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def config():
    from src.l4_data.config import get_config
    return get_config()


@pytest.fixture
def memory_manager(tmp_path):
    db_path = str(tmp_path / "test.db")
    from src.l4_data.memory_store import MemoryManager
    return MemoryManager(db_path=db_path)


@pytest.fixture
def guardrail_pipeline():
    from src.l2_guardrails import GuardrailPipeline
    return GuardrailPipeline()
