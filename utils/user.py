from datetime import datetime, timezone
from typing import List, Optional
from model import ACCESS_TYPES, Access, LearningPreference, StudyStats, User
from utils.data import get_db
from utils.progress import apply_activity

# Repository access type -> column on the users table.
USER_ACCESS_COLUMNS = {
    'accesses': 'document_accessed',
    'likes': 'liked_documents',
    'dislikes': 'disliked_documents',
    'bookmarks': 'bookmarked_documents',
    'shares': 'shared_documents',
}


def get_user(user_id: str) -> Optional[User]:
    response = get_db().table("users").select("*").eq("user_id", user_id).limit(1).execute()
    if not response.data:
        return None
    return User.from_row(response.data[0])


def list_repositories(repo_ids: List[str]) -> List[dict]:
    if not repo_ids:
        return []
    response = get_db().table('document_repositories').select('repo_id, name, documents, updated_at') \
        .in_('repo_id', repo_ids).eq('is_deleted', False).order('updated_at', desc=True).execute()
    return response.data or []


def list_histories(chat_ids: List[str]) -> List[dict]:
    if not chat_ids:
        return []
    response = get_db().table('chat_histories').select('title, last_message, created_at') \
        .in_('chat_id', chat_ids).eq('is_deleted', False).order('created_at', desc=True).execute()
    return response.data or []


def update_user_badges(user_id: str, earned_badges: List[str]) -> bool:
    update_response = get_db().table('users').update({"badges": earned_badges}).eq('user_id', user_id).execute()
    return len(update_response.data) > 0


def update_learning_preferences(user_id: str, preferences: LearningPreference) -> bool:
    response = get_db().table('users').update({"learning_preferences": preferences.model_dump()}) \
        .eq('user_id', user_id).execute()
    return len(response.data) > 0


def toggle_access(entries: List[dict], access: Access, access_type: str, opposite: Optional[List[dict]] = None) -> List[dict]:
    """Apply an access event to a list of stored Access dicts.

    Views and shares are appended every time; likes, dislikes and bookmarks toggle,
    and a like removes a dislike (and vice versa) from `opposite`, in place.
    """
    if access_type in ('accesses', 'shares'):
        return entries + [access.model_dump()]
    if opposite is not None:
        opposite[:] = [e for e in opposite if e["access_id"] != access.access_id]
    remaining = [e for e in entries if e["access_id"] != access.access_id]
    if len(remaining) == len(entries):
        remaining.append(access.model_dump())
    return remaining


def update_user_access(user_id: str, access: Access, access_type: str) -> bool:
    if access_type not in ACCESS_TYPES:
        return False
    response = get_db().table('users').select('*').eq('user_id', user_id).limit(1).execute()
    if not response.data:
        return False
    user_data = response.data[0]
    if access.access_id in (user_data.get('repositories') or []):
        return False
    columns = {key: list(user_data.get(col) or []) for key, col in USER_ACCESS_COLUMNS.items()}
    opposite = {'likes': 'dislikes', 'dislikes': 'likes'}.get(access_type)
    columns[access_type] = toggle_access(columns[access_type], access, access_type,
                                         columns[opposite] if opposite else None)
    update_data = {USER_ACCESS_COLUMNS[key]: value for key, value in columns.items()}
    update_response = get_db().table('users').update(update_data).eq('user_id', user_id).execute()
    return len(update_response.data) > 0


def update_study_stats(user_id: str, study_stat: StudyStats, is_login: bool = False) -> int:
    """Record an activity event. Returns the XP actually earned (0 on failure)."""
    db = get_db()
    response = db.table('users').select('study_stats, experience_points, daily_challenges') \
        .eq('user_id', user_id).limit(1).execute()
    if not response.data:
        return 0
    row = response.data[0]
    history, challenges, xp_earned = apply_activity(
        row.get('study_stats') or [],
        row.get('daily_challenges') or {},
        study_stat,
        datetime.now(timezone.utc),
        is_login,
    )
    update_response = db.table('users').update({
        "study_stats": history,
        "experience_points": (row.get('experience_points') or 0) + xp_earned,
        "daily_challenges": challenges,
    }).eq('user_id', user_id).execute()
    return xp_earned if update_response.data else 0
