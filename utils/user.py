import random
from datetime import datetime
from typing import List, Optional
from model import Access, LearningPreference, StudyStats, User
from utils.badge import DAILY_CHALLENGES_POOL
from utils.data import initialize_supabase

db = initialize_supabase()

def get_user(user_id: str) -> Optional[User]:
    response = db.table("users").select("*").eq("user_id", user_id).execute()
    if not response.data or len(response.data) == 0:
        return None
    user_data = response.data[0]
    return User(
        user_id=user_data["user_id"],
        username=user_data["username"],
        created_at=user_data['created_at'],
        last_login=user_data['last_login'],
        learning_preferences=LearningPreference(**user_data['learning_preferences']) if user_data['learning_preferences'] else LearningPreference(),
        document_accessed=user_data['document_accessed'],
        liked_documents=user_data['liked_documents'],
        disliked_documents=user_data['disliked_documents'],
        bookmarked_documents=user_data['bookmarked_documents'],
        shared_documents=user_data['shared_documents'],
        experience_points=user_data['experience_points'],
        profile_picture=user_data['profile_picture'],
        telegram_id=user_data['telegram_id'],
        repositories=user_data['repositories'],
        chat_histories=user_data['chat_histories'],
        badges=user_data['badges'],
        daily_challenges=user_data['daily_challenges'],
        study_stats=user_data['study_stats'],
        followers=user_data['followers'],
        following=user_data['following'],
        is_deleted=user_data['is_deleted'],
        notification_preferences=user_data['notification_preferences']
    )
    
def list_repositories(repo_ids: List[str]) -> List[dict]:
    repositories = []
    for repo_id in repo_ids:
        response = db.table('document_repositories').select('name, documents').eq('repo_id', repo_id).eq('is_deleted', False).limit(1).execute()
        repo_data = response.data[0]
        repositories.append(repo_data)
    return repositories

def list_histories(chat_ids: List[str]) -> List[dict]:
    histories = []
    for chat_id in chat_ids:
        response = db.table('chat_histories').select('title, last_message, created_at').eq('chat_id', chat_id).eq('is_deleted', False).limit(1).execute()
        chat_data = response.data[0]
        histories.append(chat_data)
    return histories

def update_user_badges(user_id: str, earned_badges: List[str]) -> bool:
    update_response = db.table('users').update({"badges": earned_badges}).eq('user_id', user_id).execute()
    return len(update_response.data) > 0

def update_user_access(user_id: str, access: Access, access_type: str) -> bool:
    response = db.table('users').select('*').eq('user_id', user_id).limit(1).execute()
    if not response.data or len(response.data) == 0 or access_type not in ['accesses', 'likes', 'dislikes', 'bookmarks', 'shares']:
        return False
    if access.access_id in response.data[0]['repositories']:
        return False
    user_data = response.data[0]
    update_data = {
        'document_accessed': user_data['document_accessed'], 
        'liked_documents': user_data['liked_documents'], 
        'disliked_documents': user_data['disliked_documents'], 
        'bookmarked_documents': user_data['bookmarked_documents'], 
        'shared_documents': user_data['shared_documents']
    }
    if access_type == 'accesses':
        update_data['document_accessed'].append(access.dict())
    elif access_type == 'likes':
        is_like = False
        for dislike in update_data['disliked_documents']:
            if dislike["access_id"] == access.access_id:
                update_data['disliked_documents'].remove(dislike)
        for like in update_data['liked_documents']:
            if like["access_id"] == access.access_id:
                is_like = True
                update_data['liked_documents'].remove(like)
        if not is_like:
            update_data['liked_documents'].append(access.dict())
    elif access_type == 'dislikes':
        is_dislike = False
        for like in update_data['liked_documents']:
            if like["access_id"] == access.access_id:
                update_data['liked_documents'].remove(like)
        for dislike in update_data['disliked_documents']:
            if dislike["access_id"] == access.access_id:
                is_dislike = True
                update_data['disliked_documents'].remove(dislike)
        if not is_dislike:
            update_data['disliked_documents'].append(access.dict())
    elif access_type == 'bookmarks':
        is_bookmark = False
        for bookmark in update_data['bookmarked_documents']:
            if bookmark["access_id"] == access.access_id:
                is_bookmark = True
                update_data['bookmarked_documents'].remove(bookmark)
        if not is_bookmark:
            update_data['bookmarked_documents'].append(access.dict())
    elif access_type == 'shares':
        update_data['shared_documents'].append(access.dict())
    update_response = db.table('users').update(update_data).eq('user_id', user_id).execute()
    return len(update_response.data) > 0

def update_study_stats(user_id: str, study_stat: StudyStats, is_login: bool = False) -> bool:
    response = db.table('users').select('study_stats, experience_points, daily_challenges').eq('user_id', user_id).limit(1).execute()
    if response.data and len(response.data) == 0:
        return None
    new_stat = study_stat
    stats = response.data[0]['study_stats']
    xp = response.data[0]['experience_points']
    challenges = response.data[0]['daily_challenges']
    xp += study_stat.xp_gained
    is_new = True
    if len(stats) != 0:
        stat_data = stats[-1]
        old_stat = StudyStats(
            total_study_time=stat_data["total_study_time"],
            documents_read=stat_data["documents_read"],
            documents_uploaded=stat_data["documents_uploaded"],
            repositories_created=stat_data["repositories_created"],
            repositories_accessed=stat_data["repositories_accessed"],
            messages_sent=stat_data["messages_sent"],
            couses_created=stat_data["couses_created"],
            quizzes_created=stat_data["quizzes_created"],
            quizzes_completed=stat_data["quizzes_completed"],
            questions_asked=stat_data["questions_asked"],
            questions_answered=stat_data["questions_answered"],
            correct_answers=stat_data["correct_answers"],
            streak_days=stat_data["streak_days"],
            challenges_completed=stat_data["challenges_completed"],
            last_activity=stat_data["last_activity"],
            subject_performance=stat_data["subject_performance"],
            xp_gained=stat_data["xp_gained"],
            chat_created=stat_data["chat_created"]
        )
        last_activity = old_stat.get_last_activity()
        last_activity_tz = last_activity.tzinfo
        now = datetime.now(last_activity_tz)
        if now.date() == last_activity.date():
            is_new = False
            if not is_login:
                new_stat.total_study_time = (now - last_activity).seconds + old_stat.total_study_time
            new_stat.challenges_completed = study_stat.challenges_completed + old_stat.challenges_completed
            new_stat.correct_answers = study_stat.correct_answers + old_stat.correct_answers
            new_stat.repositories_created = study_stat.repositories_created + old_stat.repositories_created
            new_stat.repositories_accessed = study_stat.repositories_accessed + old_stat.repositories_accessed
            new_stat.documents_uploaded = study_stat.documents_uploaded + old_stat.documents_uploaded
            new_stat.documents_read = study_stat.documents_read + old_stat.documents_read
            new_stat.questions_answered = study_stat.questions_answered + old_stat.questions_answered
            new_stat.questions_asked = study_stat.questions_asked + old_stat.questions_asked
            new_stat.quizzes_completed = study_stat.quizzes_completed + old_stat.quizzes_completed
            new_stat.quizzes_created = study_stat.quizzes_created + old_stat.quizzes_created
            new_stat.xp_gained = study_stat.xp_gained + old_stat.xp_gained
            new_stat.messages_sent = study_stat.messages_sent + old_stat.messages_sent
            new_stat.couses_created = study_stat.couses_created + old_stat.couses_created
            new_stat.chat_created = study_stat.chat_created + old_stat.chat_created
            new_stat.streak_days = old_stat.streak_days
        else:
            challenges = {"challenge_O": random.choice(DAILY_CHALLENGES_POOL), 
                      "challenge_1": random.choice(DAILY_CHALLENGES_POOL), 
                      "challenge_2": random.choice(DAILY_CHALLENGES_POOL)
                    }
            absent_day = (now - last_activity).days
            if not absent_day > 1:
                new_stat.streak_days = old_stat.streak_days + 1
    else:
        if not challenges:
            challenges = {"challenge_O": random.choice(DAILY_CHALLENGES_POOL), 
                        "challenge_1": random.choice(DAILY_CHALLENGES_POOL), 
                        "challenge_2": random.choice(DAILY_CHALLENGES_POOL)
                        }
    new_stat_data = new_stat.dict()
    for challenge_id, challenge in challenges.items():
        if new_stat_data[challenge["stat_field"]] >= challenge["target_value"] and not challenge["completed"]:
            new_stat_data["xp_gained"] += challenge["xp_reward"]
            new_stat_data["challenges_completed"] += 1
            xp += challenge["xp_reward"]
            challenges[challenge_id]["completed"] = True 
    if is_new:
        stats.append(new_stat_data)
    else:
        stats[-1] = new_stat_data
    update_response = db.table('users').update({"study_stats": stats, "experience_points": xp, "daily_challenges": challenges}).eq('user_id', user_id).execute()
    return len(update_response.data) > 0
