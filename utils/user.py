from typing import Optional
from model import LearningPreference, User
from utils.data import initialize_supabase

db = initialize_supabase()

def get_user(user_id: str) -> Optional[User]:
    """
    Récupère les informations d'un utilisateur à partir de la base de données Supabase.

    Args:
        user_id (str): L'ID de l'utilisateur.

    Returns:
        dict: Les informations de l'utilisateur.
    """
    
    # Requête pour récupérer les informations de l'utilisateur
    response = db.table("users").select("*").eq("user_id", user_id).execute()
    
    # Vérifier si des données ont été trouvées
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
        level=user_data['level'],
        profile_picture=user_data['profile_picture'],
        telegram_id=user_data['telegram_id'],
        repositories=user_data['repositories'],
        chat_histories=user_data['chat_histories'],
        achievements=user_data['achievements'],
        badges=user_data['badges'],
        daily_challenges=user_data['daily_challenges'],
        study_stats=user_data['study_stats'],
        followers=user_data['followers'],
        following=user_data['following'],
        is_deleted=user_data['is_deleted'],
        notification_preferences=user_data['notification_preferences']
    )