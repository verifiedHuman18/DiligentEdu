import random

from scripts.seed_mock_data import (
    generate_student_seed_payload,
    get_subject_chapters,
)


def test_subject_chapters_are_class_isolated():
    class9_sci = get_subject_chapters(9, "Science")
    class9_math = get_subject_chapters(9, "Mathematics")
    class10_sci = get_subject_chapters(10, "Science")
    class10_math = get_subject_chapters(10, "Mathematics")

    assert len(class9_sci) == 13
    assert len(class9_math) == 8
    assert len(class10_sci) == 13
    assert len(class10_math) == 14

    assert "Describing Motion Around Us" in class9_sci
    assert "Electrical" not in class9_sci
    assert "Electricity" in class10_sci
    assert "Real Numbers" in class10_math
    assert "Orienting Yourself: The Use of Coordinates" in class9_math

    assert set(class9_sci).isdisjoint(set(class10_sci))
    assert set(class9_math).isdisjoint(set(class10_math))


def test_generated_student_payload_respects_grade_and_subject_bounds():
    payload = generate_student_seed_payload(
        student_id="student_seed_guard", class_level=9, rng=random.Random(42)
    )

    assert 15 <= len(payload["quizzes"]) <= 30
    assert len(payload["action_plans"]) == 2
    assert len(payload["study_twins"]) == 2

    for quiz in payload["quizzes"]:
        assert quiz["class_level"] == 9
        assert quiz["chapter"] in get_subject_chapters(9, quiz["subject"])

    for plan in payload["action_plans"]:
        assert plan["class_level"] == 9
        assert plan["subject"] in {"Science", "Mathematics"}
        assert plan["focus_chapter"] in get_subject_chapters(9, plan["subject"])

    for twin in payload["study_twins"]:
        assert twin["class_level"] == 9
        assert twin["subject"] in {"Science", "Mathematics"}
        assert twin["twin_student_id"].startswith("student_")
