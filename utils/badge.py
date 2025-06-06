from typing import List, Dict
from model import Badge    

BADGES = [
      Badge(badge_id = "study_00", name =  "Rookie Learner", description = "Study for 1 hour total", icon = "⏰", badge_type = "bronze", 
            condition = lambda stats: stats["total_study_time"] >= 3600),
      Badge(badge_id = "study_01", name =  "Study Enthusiast", description = "Study for 10 hours total", icon = "📚", badge_type = "silver", 
            condition = lambda stats: stats["total_study_time"] >= 36000),
      Badge(badge_id = "study_02", name =  "Study Master", description = "Study for 50 hours total", icon = "🎓", badge_type = "gold", 
            condition = lambda stats: stats["total_study_time"] >= 180000),
      Badge(badge_id = "study_03", name =  "Study Legend", description = "Study for 100 hours total", icon = "👑", badge_type = "platinium", 
            condition = lambda stats: stats["total_study_time"] >= 360000),
      Badge(badge_id = "study_04", name =  "Study Immortal", description = "Study for 250 hours total", icon = "💎", badge_type = "diamond", 
            condition = lambda stats: stats["total_study_time"] >= 900000),
      Badge(badge_id = "reader_00", name =  "First Reader", description = "Read your first document", icon = "📖", badge_type = "bronze", 
            condition = lambda stats: stats["documents_read"] >= 1),
      Badge(badge_id = "reader_01", name =  "Bookworm", description = "Read 25 documents", icon = "🐛", badge_type = "silver", 
            condition = lambda stats: stats["documents_read"] >= 25),
      Badge(badge_id = "reader_02", name =  "Library Master", description = "Read 100 documents", icon = "📚", badge_type = "gold", 
            condition = lambda stats: stats["documents_read"] >= 100),
      Badge(badge_id = "reader_03", name =  "Knowledge Seeker", description = "Read 250 documents", icon = "🔍", badge_type = "platinium", 
            condition = lambda stats: stats["documents_read"] >= 250),
      Badge(badge_id = "reader_04", name =  "Omnilegent Sage", description = "Read 500 documents", icon = "📜", badge_type = "diamond", 
            condition = lambda stats: stats["documents_read"] >= 500),
      Badge(badge_id = "repo_00", name =  "Repository Creator", description = "Create your first repository", icon = "📁", badge_type = "bronze", 
            condition = lambda stats: stats["repositories_created"] >= 1),
      Badge(badge_id = "repo_01", name =  "Organizer", description = "Create 5 repositories", icon = "🗂️", badge_type = "silver", 
            condition = lambda stats: stats["repositories_created"] >= 5),
      Badge(badge_id = "repo_02", name =  "Knowledge Architect", description = "Create 20 repositories", icon = "🏗️", badge_type = "gold", 
            condition = lambda stats: stats["repositories_created"] >= 20),
      Badge(badge_id = "repo_03", name =  "System Designer", description = "Create 50 repositories", icon = "🧠", badge_type = "platinium", 
            condition = lambda stats: stats["repositories_created"] >= 50),
      Badge(badge_id = "repo_04", name =  "Knowledge Tycoon", description = "Create 100 repositories", icon = "💼", badge_type = "diamond", 
            condition = lambda stats: stats["repositories_created"] >= 100),
      Badge(badge_id = "explorer_00", name =  "First Repo Visit", description = "Access your first repository", icon = "👣", badge_type = "bronze", 
            condition = lambda stats: stats["repositories_accessed"] >= 1),
      Badge(badge_id = "explorer_01", name =  "Repository Explorer", description = "Access 50 repositories", icon = "🗺️", badge_type = "silver", 
            condition = lambda stats: stats["repositories_accessed"] >= 50),
      Badge(badge_id = "explorer_02", name =  "Repository Navigator", description = "Access 150 repositories", icon = "🧭", badge_type = "gold", 
            condition = lambda stats: stats["repositories_accessed"] >= 150),
      Badge(badge_id = "explorer_03", name =  "Repository Researcher", description = "Access 300 repositories", icon = "🔬", badge_type = "platinium", 
            condition = lambda stats: stats["repositories_accessed"] >= 300),
      Badge(badge_id = "explorer_04", name =  "Omniscient Miner", description = "Access 500 repositories", icon = "⛏️", badge_type = "diamond", 
            condition = lambda stats: stats["repositories_accessed"] >= 500),
      Badge(badge_id = "teacher_00", name =  "Teaching Novice", description = "Create your first course", icon = "👨‍🏫", badge_type = "bronze", 
            condition = lambda stats: stats["couses_created"] >= 1),
      Badge(badge_id = "teacher_01", name =  "Educator", description = "Create 10 courses", icon = "🎯", badge_type = "silver", 
            condition = lambda stats: stats["couses_created"] >= 10),
      Badge(badge_id = "teacher_02", name =  "Master Teacher", description = "Create 25 courses", icon = "🏆", badge_type = "gold", 
            condition = lambda stats: stats["couses_created"] >= 25),
      Badge(badge_id = "teacher_03", name =  "Curriculum Builder", description = "Create 50 courses", icon = "📘", badge_type = "platinium", 
            condition = lambda stats: stats["couses_created"] >= 50),
      Badge(badge_id = "teacher_04", name =  "Education Visionary", description = "Create 100 courses", icon = "🌟", badge_type = "diamond", 
            condition = lambda stats: stats["couses_created"] >= 100),
      Badge(badge_id = "chatter_00", name =  "First Chat", description = "Start your first conversation", icon = "💬", badge_type = "bronze", 
            condition = lambda stats: stats["chat_created"] >= 1),
      Badge(badge_id = "chatter_01", name =  "Social Butterfly", description = "Create 10 chats", icon = "🦋", badge_type = "silver", 
            condition = lambda stats: stats["chat_created"] >= 10),
      Badge(badge_id = "chatter_02", name =  "Conversation Starter", description = "Create 30 chats", icon = "🗨️", badge_type = "gold", 
            condition = lambda stats: stats["chat_created"] >= 30),
      Badge(badge_id = "chatter_03", name =  "Dialogue Driver", description = "Create 75 chats", icon = "🧭", badge_type = "platinium", 
            condition = lambda stats: stats["chat_created"] >= 75),
      Badge(badge_id = "chatter_04", name =  "Connection Master", description = "Create 150 chats", icon = "🌐", badge_type = "diamond", 
            condition = lambda stats: stats["chat_created"] >= 150),
      Badge(badge_id = "communicator_00", name =  "First Message Sent", description = "Send your first message", icon = "💬", badge_type = "bronze", 
            condition = lambda stats: stats["messages_sent"] >= 1),
      Badge(badge_id = "communicator_01", name =  "Conversationalist", description = "Send 100 messages", icon = "🗣️", badge_type = "silver", 
            condition = lambda stats: stats["messages_sent"] >= 100),
      Badge(badge_id = "communicator_02", name =  "Master Communicator", description = "Send 500 messages", icon = "📢", badge_type = "gold", 
            condition = lambda stats: stats["messages_sent"] >= 500),
      Badge(badge_id = "communicator_03", name =  "Voice Amplifier", description = "Send 1,000 messages", icon = "🎙️", badge_type = "platinium", 
            condition = lambda stats: stats["messages_sent"] >= 1000),
      Badge(badge_id = "communicator_04", name =  "Echo Champion", description = "Send 2,500 messages", icon = "📡", badge_type = "diamond", 
            condition = lambda stats: stats["messages_sent"] >= 2500),
      Badge(badge_id = "question_00", name =  "Quiz Beginner", description = "Create your first exercise", icon = "❓", badge_type = "bronze", 
            condition = lambda stats: stats["quizzes_created"] >= 1),
      Badge(badge_id = "question_01", name =  "Quiz Master", description = "Create 10 exercises", icon = "🧠", badge_type = "silver", 
            condition = lambda stats: stats["quizzes_created"] >= 10),
      Badge(badge_id = "question_02", name =  "Question Bank", description = "Create 50 exercises", icon = "🏦", badge_type = "gold", 
            condition = lambda stats: stats["quizzes_created"] >= 50),
      Badge(badge_id = "question_03", name =  "Quiz Tycoon", description = "Create 200 exercises", icon = "👑", badge_type = "platinium", 
            condition = lambda stats: stats["quizzes_created"] >= 200),
      Badge(badge_id = "question_04", name =  "Quiz Legend", description = "Create 500 exercises", icon = "💎", badge_type = "diamond", 
            condition = lambda stats: stats["quizzes_created"] >= 500),
      Badge(badge_id = "quiz_00", name =  "Quiz Novice", description = "Complete 1 exercise", icon = "🎯", badge_type = "bronze", 
            condition = lambda stats: stats["quizzes_completed"] >= 1),
      Badge(badge_id = "quiz_01", name =  "Quiz Enthusiast", description = "Complete 5 exercises", icon = "🎲", badge_type = "silver", 
            condition = lambda stats: stats["quizzes_completed"] >= 5),
      Badge(badge_id = "quiz_02", name =  "Quiz Champion", description = "Complete 25 exercises", icon = "🏅", badge_type = "gold", 
            condition = lambda stats: stats["quizzes_completed"] >= 25),
      Badge(badge_id = "quiz_03", name =  "Quiz Legend", description = "Complete 100 exercises", icon = "🏆", badge_type = "platinium", 
            condition = lambda stats: stats["quizzes_completed"] >= 100),
      Badge(badge_id = "quiz_04", name =  "Quiz Immortal", description = "Complete 500 exercises", icon = "💎", badge_type = "diamond", 
            condition = lambda stats: stats["quizzes_completed"] >= 500),
      Badge(badge_id = "careful_00", name =  "Careful", description = "Get 70% correct answers (min 10 questions)", icon = "🧐", badge_type = "bronze", 
            condition = lambda stats: stats["questions_answered"] >= 10 and stats["correct_answers"] / stats["questions_answered"] >= 0.7),
      Badge(badge_id = "careful_01", name =  "Accurate", description = "Get 80% correct answers (min 20 questions)", icon = "🎯", badge_type = "silver", 
            condition = lambda stats: stats["questions_answered"] >= 20 and stats["correct_answers"] / stats["questions_answered"] >= 0.8),
      Badge(badge_id = "careful_02", name =  "Perfectionist", description = "Get 95% correct answers (min 50 questions)", icon = "💎", badge_type = "gold", 
            condition = lambda stats: stats["questions_answered"] >= 50 and stats["correct_answers"] / stats["questions_answered"] >= 0.95),
      Badge(badge_id = "careful_03", name =  "Genius", description = "Get 98% correct answers (min 100 questions)", icon = "🧬", badge_type = "platinium", 
            condition = lambda stats: stats["questions_answered"] >= 100 and stats["correct_answers"] / stats["questions_answered"] >= 0.98),
      Badge(badge_id = "careful_04", name =  "Inhuman", description = "Get 99.5% correct answers (min 250 questions)", icon = "💠", badge_type = "diamond", 
            condition = lambda stats: stats["questions_answered"] >= 250 and stats["correct_answers"] / stats["questions_answered"] >= 0.995),
      Badge(badge_id = "routine_00", name =  "Routine Starter", description = "Study for 3 days straight", icon = "🔁", badge_type = "bronze", 
            condition = lambda stats: stats["streak_days"] >= 3),
      Badge(badge_id = "routine_01", name =  "Consistent Learner", description = "Study for 7 days straight", icon = "📅", badge_type = "silver", 
            condition = lambda stats: stats["streak_days"] >= 7),
      Badge(badge_id = "routine_02", name =  "Dedicated Student", description = "Study for 30 days straight", icon = "🔥", badge_type = "gold", 
            condition = lambda stats: stats["streak_days"] >= 30),
      Badge(badge_id = "routine_03", name =  "Unstoppable", description = "Study for 100 days straight", icon = "⚡", badge_type = "platinium", 
            condition = lambda stats: stats["streak_days"] >= 100),
      Badge(badge_id = "routine_04", name =  "Eternal Scholar", description = "Study for 365 days straight", icon = "💎", badge_type = "diamond", 
            condition = lambda stats: stats["streak_days"] >= 365),
      Badge(badge_id = "xp_00", name =  "XP Starter", description = "Gain 1000 XP", icon = "⭐", badge_type = "bronze", 
            condition = lambda stats: stats["xp_gained"] >= 1000),
      Badge(badge_id = "xp_01", name =  "XP Collector", description = "Gain 10000 XP", icon = "✨", badge_type = "silver", 
            condition = lambda stats: stats["xp_gained"] >= 10000),
      Badge(badge_id = "xp_02", name =  "XP Master", description = "Gain 50000 XP", icon = "🌟", badge_type = "gold", 
            condition = lambda stats: stats["xp_gained"] >= 50000),
      Badge(badge_id = "xp_03", name = "XP Legend", description = "Gain 100000 XP", icon = "💫", badge_type = "platinium", 
            condition = lambda stats: stats["xp_gained"] >= 100000),
      Badge(badge_id = "xp_04", name = "XP Champion", description = "Gain 500000 XP", icon = "💎", badge_type = "diamond", 
            condition = lambda stats: stats["xp_gained"] >= 500000),
      Badge(badge_id = "content_00", name = "Early Bird", description = "Upload 5 documents", icon = "🐦", badge_type = "bronze", 
            condition = lambda stats: stats["documents_uploaded"] >= 5),
      Badge(badge_id = "content_01", name = "Content Creator", description = "Upload 25 documents", icon = "📝", badge_type = "silver", 
            condition = lambda stats: stats["documents_uploaded"] >= 25),
      Badge(badge_id = "content_02", name = "Pro Uploader", description = "Upload 100 documents", icon = "📤", badge_type = "gold", 
            condition = lambda stats: stats["documents_uploaded"] >= 100),
      Badge(badge_id = "content_03", name = "Publishing Star", description = "Upload 500 documents", icon = "🌠", badge_type = "platinium", 
            condition = lambda stats: stats["documents_uploaded"] >= 500),
      Badge(badge_id = "content_04", name = "Archive Master", description = "Upload 1000 documents", icon = "💎", badge_type = "diamond", 
            condition = lambda stats: stats["documents_uploaded"] >= 1000),
      Badge(badge_id = "challenger_00", name = "Challenger", description = "Complete your first challenge", icon = "⚔️", badge_type = "bronze", 
            condition = lambda stats: stats["challenges_completed"] >= 1),
      Badge(badge_id = "challenger_01", name = "Challenge Warrior", description = "Complete 10 challenges", icon = "🛡️", badge_type = "silver", 
            condition = lambda stats: stats["challenges_completed"] >= 10),
      Badge(badge_id = "challenger_02", name = "Challenge Champion", description = "Complete 25 challenges", icon = "👑", badge_type = "gold", 
            condition = lambda stats: stats["challenges_completed"] >= 25),
      Badge(badge_id = "challenger_03", name = "Challenge Gladiator", description = "Complete 50 challenges", icon = "🏛️", badge_type = "platinium", 
            condition = lambda stats: stats["challenges_completed"] >= 50),
      Badge(badge_id = "challenger_04", name = "Mythic Challenger", description = "Complete 100 challenges", icon = "🔥", badge_type = "diamond", 
            condition = lambda stats: stats["challenges_completed"] >= 100),
]

def get_earned_badges(stats: Dict[str, float]) -> List[Badge]:
    earned_badges = []
    for badge in BADGES:
        try:
            if badge.condition(stats):
                earned_badges.append(badge)
        except (ZeroDivisionError, AttributeError):
            continue
    return earned_badges

DAILY_CHALLENGES_POOL = [
    {
        "name": "Study for at least 30 minutes today",
        "target_value": 30,
        "completed": False,
        "stat_field": "total_study_time",
        "xp_reward": 50
    },
    {
        "name": "Study for at least 60 minutes today",
        "target_value": 60,
        "completed": False,
        "stat_field": "total_study_time",
        "xp_reward": 100
    },
    {
        "name": "Study for at least 120 minutes today",
        "target_value": 120,
        "completed": False,
        "stat_field": "total_study_time",
        "xp_reward": 200
    },
    {
        "name": "Read 2 documents today",
        "target_value": 2,
        "completed": False,
        "stat_field": "documents_read",
        "xp_reward": 30
    },
    {
        "name": "Read 5 documents today",
        "target_value": 5,
        "completed": False,
        "stat_field": "documents_read",
        "xp_reward": 75
    },
    {
        "name": "Read 8 documents today",
        "target_value": 8,
        "completed": False,
        "stat_field": "documents_read",
        "xp_reward": 150
    },
    {
        "name": "Create 1 new course today",
        "target_value": 1,
        "completed": False,
        "stat_field": "couses_created",
        "xp_reward": 40
    },
    {
        "name": "Create 2 courses today",
        "target_value": 2,
        "completed": False,
        "stat_field": "couses_created",
        "xp_reward": 80
    },
    {
        "name": "Create 2 exercises today",
        "target_value": 2,
        "completed": False,
        "stat_field": "quizzes_created",
        "xp_reward": 90
    },
    {
        "name": "Create 3 exercises today",
        "target_value": 3,
        "completed": False,
        "stat_field": "quizzes_created",
        "xp_reward": 145
    },
    {
        "name": "Send 10 messages today",
        "target_value": 10,
        "completed": False,
        "stat_field": "messages_sent",
        "xp_reward": 25
    },
    {
        "name": "Send 25 messages today",
        "target_value": 25,
        "completed": False,
        "stat_field": "messages_sent",
        "xp_reward": 60
    },
    {
        "name": "Access 5 different repositories today",
        "target_value": 5,
        "completed": False,
        "stat_field": "repositories_accessed",
        "xp_reward": 70
    },
    {
        "name": "Access 2 different repositories today",
        "target_value": 2,
        "completed": False,
        "stat_field": "repositories_accessed",
        "xp_reward": 25
    },
    {
        "name": "Complete 2 exercises today",
        "target_value": 2,
        "completed": False,
        "stat_field": "quizzes_completed",
        "xp_reward": 40
    },
    {
        "name": "Answer 10 questions correctly today",
        "target_value": 10,
        "completed": False,
        "stat_field": "correct_answers",
        "xp_reward": 80
    },
    {
        "name": "Complete 5 exercises today",
        "target_value": 5,
        "completed": False,
        "stat_field": "quizzes_completed",
        "xp_reward": 120
    },
    {
        "name": "Generate 5 questions today",
        "target_value": 5,
        "completed": False,
        "stat_field": "questions_asked",
        "xp_reward": 30
    },
    {
        "name": "Answer 15 questions today",
        "target_value": 15,
        "completed": False,
        "stat_field": "questions_answered",
        "xp_reward": 85
    }
]