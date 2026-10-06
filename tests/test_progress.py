from datetime import datetime, timedelta, timezone
from model import StudyStats
from utils.progress import apply_activity

T0 = datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc)


def day(stats: dict, when: datetime) -> dict:
    return StudyStats(**stats, last_activity=when.isoformat()).model_dump()


def test_first_activity_starts_history_and_streak():
    history, challenges, xp = apply_activity([], {}, StudyStats(xp_gained=10), T0, is_login=True)
    assert len(history) == 1 and history[0]["streak_days"] == 1
    assert len(challenges) == 3
    assert xp >= 10


def test_same_day_accumulates_and_counts_study_time():
    history = [day({"messages_sent": 1, "xp_gained": 2, "total_study_time": 100, "streak_days": 4}, T0)]
    now = T0 + timedelta(minutes=10)
    history, _, xp = apply_activity(history, {}, StudyStats(messages_sent=1, xp_gained=2), now)
    assert len(history) == 1
    today = history[0]
    assert today["messages_sent"] == 2 and today["xp_gained"] == 4 and today["streak_days"] == 4
    assert today["total_study_time"] == 100 + 600
    assert today["last_activity"] == now.isoformat()
    assert xp == 2


def test_login_keeps_study_time_and_idle_gaps_are_not_counted():
    history = [day({"total_study_time": 500}, T0)]
    history, _, _ = apply_activity(history, {}, StudyStats(xp_gained=10), T0 + timedelta(minutes=5), is_login=True)
    assert history[0]["total_study_time"] == 500  # was reset to 0 before
    history, _, _ = apply_activity(history, {}, StudyStats(messages_sent=1), T0 + timedelta(hours=3))
    assert history[0]["total_study_time"] == 500


def test_next_day_extends_streak_and_renews_challenges():
    old = {"challenge_O": {"name": "x", "target_value": 1, "completed": True, "stat_field": "messages_sent", "xp_reward": 1}}
    history = [day({"streak_days": 2}, T0)]
    history, challenges, _ = apply_activity(history, old, StudyStats(), T0 + timedelta(days=1))
    assert len(history) == 2 and history[-1]["streak_days"] == 3
    assert challenges != old


def test_missed_day_resets_streak():
    history = [day({"streak_days": 9}, T0)]
    history, _, _ = apply_activity(history, {}, StudyStats(), T0 + timedelta(days=3))
    assert history[-1]["streak_days"] == 1


def test_challenge_completion_awards_xp_once():
    challenges = {"challenge_O": {"name": "Send 2", "target_value": 2, "completed": False, "stat_field": "messages_sent", "xp_reward": 25}}
    history = [day({"messages_sent": 1}, T0)]
    history, challenges, xp = apply_activity(history, challenges, StudyStats(messages_sent=1, xp_gained=2), T0 + timedelta(minutes=1))
    assert challenges["challenge_O"]["completed"] and xp == 27
    assert history[0]["challenges_completed"] == 1
    _, _, xp = apply_activity(history, challenges, StudyStats(messages_sent=1, xp_gained=2), T0 + timedelta(minutes=2))
    assert xp == 2


def test_study_time_challenges_are_in_minutes():
    challenges = {"challenge_O": {"name": "30 min", "target_value": 30, "completed": False, "stat_field": "total_study_time", "xp_reward": 50}}
    history = [day({"total_study_time": 60}, T0)]
    _, challenges, _ = apply_activity(history, challenges, StudyStats(), T0 + timedelta(minutes=1))
    assert not challenges["challenge_O"]["completed"]  # 2 minutes, not 120 "minutes"


def test_legacy_naive_timestamps():
    history = [StudyStats(streak_days=1).model_dump() | {"last_activity": "2026-03-10T08:00:00"}]
    history, _, _ = apply_activity(history, {}, StudyStats(), T0)
    assert len(history) == 1
