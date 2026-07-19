import pytest

from cogito_mill.agents import agent_runtime_name
from cogito_mill.pipelines import pipeline_stages


@pytest.mark.integration
def test_runtime_identity() -> None:
    assert "langgraph" in agent_runtime_name()
    assert "publish" in pipeline_stages()
