from datetime import datetime
import uuid
from typing import Callable, List, Dict, Optional, Any
from pydantic import BaseModel, Field

class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    received_at: str = Field(default_factory=datetime.now().isoformat)
    content: str
    is_assistant: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    score: Dict[str, Any] = Field(default_factory= dict)
    
    def get_received_at(self) -> datetime:
        return datetime.fromisoformat(self.received_at)
    
class Access(BaseModel):
    access_id: str
    access_time: str = Field(default_factory=datetime.now().isoformat)
    
    def get_access_time(self) -> datetime:
        return datetime.fromisoformat(self.access_time)
    
class Chunk(BaseModel):
    text: str
    embedding: List[float] = Field(default_factory=list)
    page: int
    position: int

class LearningPreference(BaseModel):
    preferred_document: str = Field(default="")
    preferred_language: str = Field(default="en")
    preferred_subjects: List[str] = Field(default_factory=list)
    learning_style: str = Field(default="visual")
    daily_study_time: int = Field(default=0)
    difficulty_level: str = Field(default="beginner")
    preferred_content_types: List[str] = Field(default_factory=list)
    
class Document(BaseModel):
    doc_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str = ""
    file_size: int
    file_path: str
    upload_date: str = Field(default_factory=datetime.now().isoformat)
    category: Optional[str] = None
    original_repo: str
    type: str = Field(default="simple_text")
    cover: Optional[str] = None
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    owner_id: str
    is_deleted: bool = Field(default=False)
    related_documents: List[str] = Field(default_factory=list)
    
    def get_upload_date(self) -> datetime:
        return datetime.fromisoformat(self.upload_date)

class DocumentRepository(BaseModel):
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
    banner: Optional[str] = None
    accesses: List[Access] = Field(default_factory=list)
    likes: List[Access] = Field(default_factory=list)
    dislikes: List[Access] = Field(default_factory=list)
    bookmarks: List[Access] = Field(default_factory=list)
    shares: List[Access] = Field(default_factory=list)
    number_of_indexed: int = 0 
    related_repositories: List[str] = Field(default_factory=list)
    
    def get_created_at(self) -> datetime:
        return datetime.fromisoformat(self.created_at)
    
    def get_updated_at(self) -> datetime:
        return datetime.fromisoformat(self.updated_at)
    
    def last_accessed(self, user_id: str, access_type: str) -> Optional[datetime]:
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
    
    def get_document_stats(self) -> Dict[str, Any]:
        return {
            "document_count": len(self.documents),
            "access_count": len(self.accesses),
            "pertinence_count": len(self.likes) - len(self.dislikes),
            "indexed_count": self.number_of_indexed,
            "shared_count": len(self.shares),
            "saved_count": len(self.bookmarks)
        }

class ChatHistory(BaseModel):
    chat_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_id: str
    title: str = "New Conversation"
    created_at: str = Field(default_factory=datetime.now().isoformat)
    last_message: Optional[Message] = None
    messages: List[str] = Field(default_factory=list)
    repo_source: str 
    type: str
    is_deleted: bool = Field(default=False)
    mode: bool = Field(default=False)
    
    def get_created_at(self) -> datetime:
        return datetime.fromisoformat(self.created_at)
    
class StudyStats(BaseModel):
    total_study_time: int = 0
    documents_read: int = 0
    repositories_created: int = 0
    repositories_accessed: int = 0
    documents_uploaded: int = 0
    couses_created: int = 0
    messages_sent: int = 0
    chat_created: int = 0
    quizzes_created: int = 0
    quizzes_completed: int = 0
    questions_answered: int = 0
    questions_asked: int = 0
    correct_answers: int = 0
    streak_days: int = 0
    challenges_completed: int = 0
    xp_gained: int = 0
    last_activity: str = Field(default_factory=datetime.now().isoformat)
    subject_performance: Dict[str, float] = Field(default_factory=dict)
    
    def get_last_activity(self) -> datetime:
        return datetime.fromisoformat(self.last_activity)
    
class Badge(BaseModel):
    badge_id: str 
    name: str
    description: str
    icon: str
    badge_type: str
    condition: Callable

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    profile_picture: Optional[str] = None
    created_at: str = Field(default_factory=datetime.now().isoformat)
    last_login: Optional[str] = None
    learning_preferences: LearningPreference = Field(default_factory=LearningPreference)
    repositories: List[str] = Field(default_factory=list)
    document_accessed: List[Access] = Field(default_factory=list)
    liked_documents: List[Access] = Field(default_factory=list)
    disliked_documents: List[Access] = Field(default_factory=list)
    bookmarked_documents: List[Access] = Field(default_factory=list)
    shared_documents: List[Access] = Field(default_factory=list)
    chat_histories: List[str] = Field(default_factory=list)
    experience_points: int = 0
    badges: List[str] = Field(default_factory=list)
    daily_challenges: Dict[str, Any] = Field(default_factory=dict)
    study_stats: List[StudyStats] = Field(default_factory=list)
    followers: List[str] = Field(default_factory=list)
    following: List[str] = Field(default_factory=list)
    is_deleted: bool = Field(default=False)
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
        return datetime.fromisoformat(self.created_at)
    
    def get_last_login(self) -> Optional[datetime]:
        if self.last_login:
            return datetime.fromisoformat(self.last_login)
        return None
    
    def calculate_level(self, is_next: bool = False) -> int:
        level = 1
        xp_required = 100
        while self.experience_points >= xp_required:
            level += 1
            xp_required += 100 * level
        return level if not is_next else xp_required
    
    def get_total_stats(self) -> Dict[str, float]:
        if not self.study_stats:
            return {}
        total_stats = StudyStats()
        for stats in self.study_stats:
            total_stats.total_study_time += stats.total_study_time
            total_stats.documents_read += stats.documents_read
            total_stats.repositories_created += stats.repositories_created
            total_stats.repositories_accessed += stats.repositories_accessed
            total_stats.documents_uploaded += stats.documents_uploaded
            total_stats.couses_created += stats.couses_created
            total_stats.messages_sent += stats.messages_sent
            total_stats.chat_created += stats.chat_created
            total_stats.quizzes_created += stats.quizzes_created
            total_stats.quizzes_completed += stats.quizzes_completed
            total_stats.questions_answered += stats.questions_answered
            total_stats.questions_asked += stats.questions_asked
            total_stats.correct_answers += stats.correct_answers
            total_stats.challenges_completed += stats.challenges_completed
            total_stats.xp_gained += stats.xp_gained
            if stats.streak_days > total_stats.streak_days:
                total_stats.streak_days = stats.streak_days
        return {
            "total_study_time": total_stats.total_study_time,
            "documents_read": total_stats.documents_read,
            "repositories_created": total_stats.repositories_created,
            "repositories_accessed": total_stats.repositories_accessed,
            "documents_uploaded": total_stats.documents_uploaded,
            "couses_created": total_stats.couses_created,
            "messages_sent": total_stats.messages_sent,
            "chat_created": total_stats.chat_created,
            "quizzes_created": total_stats.quizzes_created,
            "quizzes_completed": total_stats.quizzes_completed,
            "questions_answered": total_stats.questions_answered,
            "questions_asked": total_stats.questions_asked,
            "correct_answers": total_stats.correct_answers,
            "streak_days": total_stats.streak_days,
            "challenges_completed": total_stats.challenges_completed,
            "xp_gained": total_stats.xp_gained
        }
