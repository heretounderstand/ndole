from datetime import datetime
import uuid
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Modèle pour les accès aux documents"""
    received_at: str = Field(default_factory=datetime.now().isoformat)
    content: str  # Contenu du message
    is_assistant: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    score: Optional[int] = None  # Score de pertinence du message
    
    def get_received_at(self) -> datetime:
        """Retourne la date et l'heure de réception"""
        return datetime.fromisoformat(self.received_at)
    
class Access(BaseModel):
    """Modèle pour les accès aux documents"""
    access_id: str
    access_time: str = Field(default_factory=datetime.now().isoformat)
    
    def get_access_time(self) -> datetime:
        """Retourne la date et l'heure d'accès"""
        return datetime.fromisoformat(self.access_time)
    
class Chunk(BaseModel):
    text: str
    embedding: List[float] = Field(default_factory=list)  # Représentation vectorielle du texte
    page: int  # Numéro de page dans le document
    position: int  # Position dans le page

class LearningPreference(BaseModel):
    """Modèle pour les préférences d'apprentissage de l'utilisateur"""
    preferred_document: str = Field(default="")
    preferred_language: str = Field(default="en")
    preferred_subjects: List[str] = Field(default_factory=list)
    learning_style: str = Field(default="visual")  # visuel, auditif, kinesthésique
    daily_study_time: int = Field(default=0)  # minutes
    difficulty_level: str = Field(default="beginner")  # débutant, intermédiaire, avancé
    preferred_content_types: List[str] = Field(default_factory=list)
    
class Document(BaseModel):
    """Modèle pour un document dans la plateforme Ndolè"""
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    file_size: int  # taille en octets
    file_path: str
    upload_date: str = Field(default_factory=datetime.now().isoformat)
    category: Optional[str] = None  # Catégorie du document
    original_repo: str
    type: str = Field(default="simple_text")
    cover: Optional[str] = None  # URL de l'image de couverture

    accesses: List[Access] = Field(default_factory=list)  # IDs des utilisateurs qui ont vu le document
    likes: List[Access] = Field(default_factory=list)  # IDs des utilisateurs qui ont aimé le document
    dislikes: List[Access] = Field(default_factory=list)  # IDs des utilisateurs qui n'ont pas aimé le document
    bookmarks: List[Access] = Field(default_factory=list)  # IDs des utilisateurs qui ont marqué le document
    shares: List[Access] = Field(default_factory=list)  # IDs des utilisateurs qui ont partagé le document
    number_of_indexed: int = 0  # Nombre d'indexations du document
    
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    owner_id: str
    is_deleted: bool = Field(default=False)
    
    related_documents: List[str] = Field(default_factory=list)  # IDs des documents liés
    
    def get_upload_date(self) -> datetime:
        """Retourne la date et l'heure de téléchargement"""
        return datetime.fromisoformat(self.upload_date)
    
    def last_accessed(self, user_id: str, access_type: str) -> Optional[datetime]:
        """Retourne la dernière date d'accès au document de l'utilisateur"""
        if access_type not in ['accesses', 'likes', 'dislikes', 'bookmarks', 'shares']:
            return False
        
        if access_type == 'accesses':
            return max((access.get_access_time() for access in self.accesses if access.access_id == user_id), default=None)
        elif access_type == 'likes':
            for access in self.likes:
                if access.access_id == user_id:
                    return access.get_access_time()
        elif access_type == 'dislikes':
            for access in self.dislikes:
                if access.access_id == user_id:
                    return access.get_access_time()
        elif access_type == 'bookmarks':
            for access in self.bookmarks:
                if access.access_id == user_id:
                    return access.get_access_time()
        elif access_type == 'shares':
            return max((access.get_access_time() for access in self.shares if access.access_id == user_id), default=None)
        return None

class DocumentRepository(BaseModel):
    """Modèle pour un dépôt de documents"""
    repo_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    is_public: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    owner_id: str
    created_at: str = Field(default_factory=datetime.now().isoformat)
    updated_at: str = Field(default_factory=datetime.now().isoformat)
    categories: List[str] = Field(default_factory=list)
    documents: List[str] = Field(default_factory=list)
    banner: Optional[str] = None  # URL de la bannière du dépôt
    
    def get_created_at(self) -> datetime:
        """Retourne la date et l'heure actuelles"""
        return datetime.fromisoformat(self.created_at)
    
    def get_updated_at(self) -> datetime:
        """Retourne la date et l'heure de la dernière modification"""
        return datetime.fromisoformat(self.updated_at)

class ChatHistory(BaseModel):
    """Modèle pour l'historique de conversation"""
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    title: str = "New Conversation"
    created_at: str = Field(default_factory=datetime.now().isoformat)
    last_message: str = Field(default_factory=datetime.now().isoformat)
    messages: List[Message] = Field(default_factory=list)
    repo_source: str 
    type: str
    is_deleted: bool = Field(default=False)
    
    def get_average_score(self) -> float:
        """Retourne le score moyen de la conversation"""
        if not self.messages:
            return 0.0
        return sum(msg.score for msg in self.messages if msg.score is not None) / len(self.messages)
    
    def get_created_at(self) -> datetime:
        """Retourne la date et l'heure de création"""
        return datetime.fromisoformat(self.created_at)
    
    def get_last_message(self) -> datetime:
        """Retourne la date et l'heure du dernier message"""
        return datetime.fromisoformat(self.last_message)

class Achievement(BaseModel):
    """Modèle pour les accomplissements et badges"""
    achievement_id: str
    name: str
    description: str
    icon_url: str = ""
    unlocked_at: Optional[datetime] = None
    
class StudyStats(BaseModel):
    """Modèle pour le suivi des statistiques d'étude"""
    total_study_time: int = 0  # minutes
    documents_read: int = 0
    quizzes_completed: int = 0
    questions_asked: int = 0
    correct_answers: int = 0
    exercises_completed: int = 0
    streak_days: int = 0
    last_activity: datetime = Field(default_factory=datetime.now)
    subject_performance: Dict[str, float] = Field(default_factory=dict)  # sujet: score moyen

class User(BaseModel):
    """Modèle principal de l'utilisateur pour la plateforme Ndolè"""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    profile_picture: Optional[str] = None
    created_at: str = Field(default_factory=datetime.now().isoformat)
    last_login: Optional[str] = None
    
    # Préférences d'apprentissage
    learning_preferences: LearningPreference = Field(default_factory=LearningPreference)
    
    # Gestion des dépôts de documents
    repositories: List[str] = Field(default_factory=list)
    document_accessed: List[Access] = Field(default_factory=list)
    liked_documents: List[str] = Field(default_factory=list)  # IDs des documents aimés
    disliked_documents: List[str] = Field(default_factory=list)  # IDs des documents non aimés
    bookmarked_documents: List[str] = Field(default_factory=list)  # IDs des documents marqués
    shared_documents: List[str] = Field(default_factory=list)  # IDs des documents partagés
    
    # Historique des conversations
    chat_histories: List[str] = Field(default_factory=list)
    
    # Système de gamification
    experience_points: int = 0
    level: int = 1
    achievements: List[Achievement] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)
    daily_challenges: Dict[str, bool] = Field(default_factory=dict)
    
    # Suivi et analyse
    study_stats: List[StudyStats] = Field(default_factory=list)
    
    followers: List[str] = Field(default_factory=list)
    following: List[str] = Field(default_factory=list)
    is_deleted: bool = Field(default=False)
    
    # Intégration Telegram
    telegram_id: Optional[str] = None
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {
            "study_reminders": True,
            "new_content": True,
            "achievement_alerts": True,
            "challenge_reminders": True,
        }
    )
    
    def get_created_at(self) -> datetime:
        """Retourne la date et l'heure actuelles"""
        return datetime.fromisoformat(self.created_at)
    
    def get_last_login(self) -> Optional[datetime]:
        """Retourne la date et l'heure de la dernière connexion"""
        if self.last_login:
            return datetime.fromisoformat(self.last_login)
        return None
    
    def add_chat_history(self, title: str = "Nouvelle conversation", document_sources: List[str] = None) -> str:
        """Crée un nouvel historique de conversation et retourne son ID"""
        if document_sources is None:
            document_sources = []
            
        chat = ChatHistory(title=title, document_sources=document_sources)
        self.chat_histories.append(chat)
        return chat.conversation_id
    
    def add_achievement(self, achievement_id: str, name: str, description: str, icon_url: str = "") -> None:
        """Ajoute un accomplissement au profil utilisateur"""
        achievement = Achievement(
            achievement_id=achievement_id,
            name=name,
            description=description,
            icon_url=icon_url,
            unlocked_at=datetime.now()
        )
        self.achievements.append(achievement)
        
    def update_study_stats(self, stats_update: Dict[str, Any]) -> None:
        """Met à jour les statistiques d'étude de l'utilisateur"""
        for key, value in stats_update.items():
            if hasattr(self.study_stats, key):
                current_value = getattr(self.study_stats, key)
                
                # Pour les dictionnaires, mise à jour au lieu de remplacement
                if isinstance(current_value, dict) and isinstance(value, dict):
                    current_value.update(value)
                # Pour les valeurs numériques, addition au lieu de remplacement
                elif isinstance(current_value, (int, float)) and isinstance(value, (int, float)):
                    setattr(self.study_stats, key, current_value + value)
                # Pour les autres types, simple remplacement
                else:
                    setattr(self.study_stats, key, value)
        
        # Mettre à jour la date de dernière activité
        self.study_stats.last_activity = datetime.now()
    
    def calculate_level(self) -> int:
        """Calcule le niveau utilisateur en fonction des points d'expérience"""
        # Formule simple : chaque niveau requiert 100 * niveau points pour passer au suivant
        level = 1
        xp_required = 100
        
        while self.experience_points >= xp_required:
            level += 1
            xp_required += 100 * level
            
        self.level = level
        return level
    
    def add_experience(self, points: int) -> Dict[str, Any]:
        """Ajoute des points d'expérience et retourne les informations de niveau"""
        old_level = self.level
        self.experience_points += points
        new_level = self.calculate_level()
        
        level_up = new_level > old_level
        
        return {
            "points_added": points,
            "total_points": self.experience_points,
            "current_level": new_level,
            "level_up": level_up,
            "next_level_points": 100 * (new_level + 1)
        }