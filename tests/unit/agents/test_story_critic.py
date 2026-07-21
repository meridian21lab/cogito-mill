"""Story critic and narrative quality unit tests."""

from __future__ import annotations

from cogito_mill.agents.critics import critique_story_document, load_prompt
from cogito_mill.domain.narrative import SceneDraft, Sentence, StoryDocument
from cogito_mill.domain.questions import QuestionBundle, ScoredQuestion
from cogito_mill.domain.recipe import DifficultyBucket, GenerationRecipe, SettingFamily
from cogito_mill.pipelines.templates import (
    _story_contains_full_name,
    build_access_timeline,
)


def _bundle(seed: int = 42):
    recipe = GenerationRecipe(
        id="r",
        seed=seed,
        provider_family="azure",
        setting_family=SettingFamily.WORKPLACE,
        difficulty_bucket=DifficultyBucket.HARD,
        n_suspects=4,
        n_distractors=3,
    )
    return build_access_timeline(recipe)


def test_generated_story_passes_critic() -> None:
    bundle = _bundle(42)
    report = critique_story_document(bundle.story, bundle.questions)
    assert report.decision == "accept", report.feedback
    assert 2 <= len(bundle.questions.questions) <= 4
    assert "Personnel index:" not in bundle.story.full_text.split("\n\n")[0]
    assert bundle.story.full_text.count("Personnel index:") <= 2
    assert "full name" in bundle.questions.main_question.lower()
    # Answer given name is shared with another cast member (blocks first-name shortcuts).
    answer = bundle.questions.gold_answer
    first = answer.split()[0]
    person_labels = [e.label for e in bundle.world.entities if e.type == "person"]
    assert sum(1 for lab in person_labels if lab.split()[0] == first) >= 2
    assert "surname" in bundle.story.full_text.lower()
    assert not _story_contains_full_name(
        bundle.story.full_text, bundle.questions.gold_answer
    )


def test_critic_rejects_personnel_dump() -> None:
    dump = "Personnel index: EMP-1 resolves to A B. " * 20
    story = StoryDocument(
        id="s",
        title="t",
        scenes=[SceneDraft(id="sc1", title="x", prose=dump)],
        sentences=[Sentence(id="sent-1", text=dump.strip())],
        full_text=dump,
    )
    questions = QuestionBundle(
        main_question="Provide the full name of the person who acted.",
        gold_answer="A B",
        questions=[
            ScoredQuestion(
                id="q1",
                question="Provide the full name of the person who acted.",
                gold_answer="A B",
                gold_answer_variants=["A B", "B, A"],
                question_type="main",
            ),
            ScoredQuestion(
                id="q2",
                question="Provide the full name of the lender.",
                gold_answer="C D",
                gold_answer_variants=["C D"],
                question_type="intermediate",
            ),
        ],
    )
    report = critique_story_document(story, questions)
    assert report.decision == "reject"
    failed = {f.gate for f in report.findings if not f.passed}
    assert "identifier_budget" in failed or "no_personnel_dump" in failed


def test_prompts_exist() -> None:
    text = load_prompt("story_critic_v1.md")
    assert "full name" in text.lower()
    assert "identifier" in text.lower()
