"""Pack-level quality metric tests."""

from cogito_mill.eval.quality import assess_dataset


def _row(index: int) -> dict[str, object]:
    unique = f"opening-{index}"
    paragraphs = []
    for paragraph in range(5):
        sentences = []
        for sentence in range(5):
            words = [
                unique,
                f"scene-{paragraph}",
                "before",
                "after",
                "around",
                "2",
                "PM",
                "minute",
                *[f"token-{index}-{paragraph}-{sentence}-{word}" for word in range(19)],
            ]
            sentences.append(" ".join(words) + ".")
        paragraphs.append(" ".join(sentences))
    return {
        "id": f"item-{index}",
        "story": "\n\n".join(paragraphs),
        "question": f"Which full name resolves concept variant {index}?",
        "n_hops": 12,
        "template_id": f"family-{index % 6}",
        "setting_family": f"setting-{index % 6}",
    }


def test_balanced_varied_pack_passes() -> None:
    report = assess_dataset([_row(index) for index in range(12)])

    assert report["passed"]
    assert len(report["dataset_sha256"]) == 64
    assert report["diversity"]["template_effective_count"] == 6.0


def test_formulaic_ledger_pack_fails() -> None:
    rows = []
    for index in range(12):
        row = _row(index)
        ledger = (
            "For this incident, the board declared the coherent signal bearer protocol active. "
            "They also fixed one shared status scale for the whole inquiry: clear counted as 0; "
            "dormant counted as 1. The tally began at 6. At each stream they squared the current "
            "tally, added coefficients 11, 13, 5, and kept the remainder modulo 97."
        )
        row["story"] = row["story"] + "\n\n" + ledger
        rows.append(row)

    report = assess_dataset(rows)

    assert not report["passed"]
    assert not report["gates"]["no_formulaic_ledger"]


def test_duplicate_and_template_monopoly_fail() -> None:
    row = _row(0)
    rows = [{**row, "id": f"copy-{index}"} for index in range(12)]

    report = assess_dataset(rows)

    assert not report["passed"]
    assert not report["gates"]["no_exact_duplicates"]
    assert not report["gates"]["template_count"]
