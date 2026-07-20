"""E2E tests require secrets and live providers — gated by marker."""

import pytest


@pytest.mark.e2e
def test_e2e_placeholder() -> None:
    pytest.skip("E2E mill runs land after architecture is grilled")
