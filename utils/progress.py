"""Pure study-statistics bookkeeping (no database access, so it is unit-testable)."""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from model import COUNTER_FIELDS, StudyStats
from utils.badge import challenge_progress_value, pick_daily_challenges

# Two events further apart than this are treated as separate study sessions,
# so idle time (e.g. a tab left open overnight) is not counted as study time.
SESSION_GAP = timedelta(minutes=30)


def apply_activity(
    history: List[Dict[str, Any]],
    challenges: Dict[str, dict],
    event: StudyStats,
    now: datetime,
    is_login: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, dict], int]:
    """Merge one activity event into the per-day stats history.

    Returns the updated history, the (possibly renewed) daily challenges and the
    total XP earned by this event, challenge rewards included.
    """
    history = list(history or [])
    challenges = dict(challenges or {})
    today = event.model_copy(update={"last_activity": now.isoformat()})
    xp = event.xp_gained
    same_day = False
    if history:
        previous = StudyStats(**history[-1])
        last = previous.get_last_activity()
        same_day = last.date() == now.date()
        if same_day:
            for name in COUNTER_FIELDS:
                setattr(today, name, getattr(previous, name) + getattr(event, name))
            today.streak_days = previous.streak_days
            today.subject_performance = {**previous.subject_performance, **event.subject_performance}
            gap = now - last
            if not is_login and timedelta(0) < gap <= SESSION_GAP:
                today.total_study_time += int(gap.total_seconds())
        else:
            consecutive = (now.date() - last.date()).days == 1
            today.streak_days = previous.streak_days + 1 if consecutive else 1
            challenges = pick_daily_challenges()
    else:
        today.streak_days = 1
        if not challenges:
            challenges = pick_daily_challenges()
    stats = today.model_dump()
    for challenge in challenges.values():
        if not challenge.get("completed") and challenge_progress_value(challenge, stats) >= challenge["target_value"]:
            challenge["completed"] = True
            stats["xp_gained"] += challenge["xp_reward"]
            stats["challenges_completed"] += 1
            xp += challenge["xp_reward"]
    if same_day:
        history[-1] = stats
    else:
        history.append(stats)
    return history, challenges, xp
