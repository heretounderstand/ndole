from datetime import datetime, timezone
import time
from model import Badge, Message, StudyStats, User, parse_dt
from utils.badge import BADGES, DAILY_CHALLENGES_POOL, get_earned_badges, pick_daily_challenges


def test_default_timestamps_are_not_frozen():
    first = Message(chat_id="c", content="a")
    time.sleep(0.01)
    second = Message(chat_id="c", content="b")
    assert first.received_at != second.received_at


def test_parse_dt_treats_naive_as_utc():
    assert parse_dt("2024-05-01T10:00:00").tzinfo == timezone.utc
    assert parse_dt("2024-05-01T10:00:00+01:00").utcoffset().total_seconds() == 3600


def test_levels_match_original_thresholds():
    # Level 2 at 100 XP, level 3 at 300, level 4 at 600 (unchanged from the original rules).
    for xp, level, next_threshold in [(0, 1, 100), (99, 1, 100), (100, 2, 300), (299, 2, 300), (300, 3, 600), (600, 4, 1000)]:
        user = User(username="u", experience_points=xp)
        assert user.calculate_level() == level
        assert user.calculate_level(is_next=True) == next_threshold


def test_level_progress():
    assert User(username="u", experience_points=200).level_progress() == 0.5


def test_total_stats():
    user = User(username="u", study_stats=[StudyStats(messages_sent=2, streak_days=3), StudyStats(messages_sent=5, streak_days=1)])
    totals = user.get_total_stats()
    assert totals["messages_sent"] == 7
    assert totals["streak_days"] == 3
    assert User(username="u").get_total_stats() == {}


def test_user_from_row_ignores_nulls_and_unknown_columns():
    user = User.from_row({"user_id": "1", "username": "bob", "badges": None, "extra": 1, "learning_preferences": None})
    assert user.badges == [] and user.learning_preferences.preferred_language == "en"


def test_badges_unique_and_well_formed():
    assert len({b.badge_id for b in BADGES}) == len(BADGES) == 70
    for badge in BADGES:
        assert badge.stat_field == "accuracy" or badge.stat_field in StudyStats.model_fields


def test_badge_thresholds():
    earned = {b.badge_id for b in get_earned_badges({"documents_read": 25, "questions_answered": 10, "correct_answers": 7})}
    assert {"reader_00", "reader_01", "careful_00"} <= earned
    assert "reader_02" not in earned and "careful_01" not in earned
    assert get_earned_badges({}) == []


def test_accuracy_badge_progress_without_answers_is_zero():
    badge = next(b for b in BADGES if b.badge_id == "careful_00")
    assert badge.progress({"questions_answered": 0, "correct_answers": 0}) == 0
    assert 0 < badge.progress({"questions_answered": 5, "correct_answers": 5}) < 1


def test_badge_progress_is_capped():
    badge = Badge(badge_id="t", name="t", description="", icon="", badge_type="bronze", stat_field="messages_sent", target=10)
    assert badge.progress({"messages_sent": 50}) == 1.0


def test_pick_daily_challenges_are_distinct_copies():
    challenges = pick_daily_challenges()
    assert len({c["name"] for c in challenges.values()}) == 3
    for c in challenges.values():
        c["completed"] = True
    assert not any(c["completed"] for c in DAILY_CHALLENGES_POOL)


def test_now_is_timezone_aware():
    before = datetime.now(timezone.utc)
    stamp = StudyStats().get_last_activity()
    assert stamp.tzinfo is not None and stamp >= before
