import pytest

from cogito_mill.llm.providers import build_chat


def test_build_chat_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unknown provider"):
        build_chat("nope")
