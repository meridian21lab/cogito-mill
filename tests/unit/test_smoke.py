from cogito_mill.datasets import hub_dataset_id
from cogito_mill.validation import is_nonempty


def test_hub_dataset_id() -> None:
    assert hub_dataset_id("reasoning-stories") == "ksopyla/reasoning-stories"


def test_is_nonempty() -> None:
    assert is_nonempty("a")
    assert not is_nonempty("  ")
