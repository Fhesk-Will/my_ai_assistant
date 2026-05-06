import pytest
from unittest.mock import MagicMock, patch

from src.l3_cognition.graph import build_graph, CognitionEngine
from src.l2_guardrails import GuardrailPipeline
from src.l4_data.memory_store import MemoryManager


class TestGraph:
    """LangGraph 流程测试"""

    def test_graph_compiles(self, tmp_path):
        mock_llm = MagicMock()
        mock_llm.get_response.return_value = "test reply"

        db_path = str(tmp_path / "test.db")
        memory = MemoryManager(db_path=db_path)
        guardrail = GuardrailPipeline()

        graph = build_graph(mock_llm, memory, None, guardrail)
        assert graph is not None

    def test_graph_invoke(self, tmp_path):
        mock_llm = MagicMock()
        mock_llm.get_response.return_value = "graph test reply"

        db_path = str(tmp_path / "test.db")
        memory = MemoryManager(db_path=db_path)
        guardrail = GuardrailPipeline()

        graph = build_graph(mock_llm, memory, None, guardrail)

        result = graph.invoke({
            "message": "hello",
            "session_id": "graph_test",
            "history": [],
            "context": "",
            "response": "",
            "metrics": {},
            "guardrail_input": {},
            "guardrail_output": {},
        })

        assert result["response"] == "graph test reply"
