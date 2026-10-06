from datetime import datetime, timezone
import uuid
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


def now_iso() -> str:
    # Must be called per instance: `datetime.now().isoformat` passed as a factory
    # was bound at import time, freezing every default timestamp.
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: str) -> datetime:
    """Parse an ISO timestamp; legacy naive values are treated as UTC."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class Message(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str
    received_at: str = Field(default_factory=now_iso)
    content: str
    is_assistant: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    score: Dict[str, Any] = Field(default_factory=dict)

    def get_received_at(self) -> datetime:
        return parse_dt(self.received_at)


class Access(BaseModel):
    access_id: str
    access_time: str = Field(default_factory=now_iso)

    def get_access_time(self) -> datetime:
        return parse_dt(self.access_time)


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
    upload_date: str = Field(default_factory=now_iso)
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
        return parse_dt(self.upload_date)


ACCESS_TYPES = ('accesses', 'likes', 'dislikes', 'bookmarks', 'shares')


class DocumentRepository(BaseModel):
    repo_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    is_public: bool = Field(default=False)
    is_deleted: bool = Field(default=False)
    owner_id: str
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)
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
        return parse_dt(self.created_at)

    def get_updated_at(self) -> datetime:
        return parse_dt(self.updated_at)

    def last_accessed(self, user_id: str, access_type: str) -> Optional[datetime]:
        if access_type not in ACCESS_TYPES:
            return None
        times = (a.get_access_time() for a in getattr(self, access_type) if a.access_id == user_id)
        return max(times, default=None)

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
    created_at: str = Field(default_factory=now_iso)
    last_message: Optional[Message] = None
    messages: List[str] = Field(default_factory=list)
    repo_source: str
    type: str
    is_deleted: bool = Field(default=False)
    mode: bool = Field(default=False)

    def get_created_at(self) -> datetime:
        return parse_dt(self.created_at)


class StudyStats(BaseModel):
    total_study_time: int = 0
    documents_read: int = 0
    repositories_created: int = 0
    repositories_accessed: int = 0
    documents_uploaded: int = 0
    # The "couses" typo is kept on purpose: it is the key stored in the database.
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
    last_activity: str = Field(default_factory=now_iso)
    subject_performance: Dict[str, float] = Field(default_factory=dict)

    def get_last_activity(self) -> datetime:
        return parse_dt(self.last_activity)


# Counters that add up from one event to the next (every int field except the streak).
COUNTER_FIELDS = [
    name for name, field in StudyStats.model_fields.items()
    if field.annotation is int and name != "streak_days"
]


class Badge(BaseModel):
    badge_id: str
    name: str
    description: str
    icon: str
    badge_type: str
    # A StudyStats counter, or "accuracy" for the correct/answered ratio.
    stat_field: str
    target: float
    # Accuracy badges only count once this many questions have been answered.
    min_questions: int = 0

    def progress(self, stats: Dict[str, float]) -> float:
        """Progress toward the badge, in [0, 1]."""
        if not stats:
            return 0.0
        if self.stat_field == "accuracy":
            answered = stats.get("questions_answered", 0)
            if answered == 0:
                return 0.0
            accuracy = stats.get("correct_answers", 0) / answered
            return min(answered / self.min_questions, 1.0) * min(accuracy / self.target, 1.0)
        return min(stats.get(self.stat_field, 0) / self.target, 1.0)

    def is_earned(self, stats: Dict[str, float]) -> bool:
        if not stats:
            return False
        if self.stat_field == "accuracy":
            answered = stats.get("questions_answered", 0)
            return answered >= self.min_questions and stats.get("correct_answers", 0) / answered >= self.target
        return stats.get(self.stat_field, 0) >= self.target


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    profile_picture: Optional[str] = None
    created_at: str = Field(default_factory=now_iso)
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

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "User":
        """Build a User from a `users` table row, ignoring NULL columns."""
        data = {k: v for k, v in row.items() if v is not None and k in cls.model_fields}
        return cls(**data)

    def get_created_at(self) -> datetime:
        return parse_dt(self.created_at)

    def get_last_login(self) -> Optional[datetime]:
        if self.last_login:
            return parse_dt(self.last_login)
        return None

    @staticmethod
    def xp_threshold(level: int) -> int:
        """Total XP needed to reach `level`: 0, 100, 300, 600, ... (+100 per level)."""
        return 50 * level * (level - 1)

    def calculate_level(self, is_next: bool = False) -> int:
        level = 1
        while self.experience_points >= self.xp_threshold(level + 1):
            level += 1
        return level if not is_next else self.xp_threshold(level + 1)

    def level_progress(self) -> float:
        """Fraction of the way from the current level to the next one, in [0, 1]."""
        level = self.calculate_level()
        start, end = self.xp_threshold(level), self.xp_threshold(level + 1)
        return min(max((self.experience_points - start) / (end - start), 0.0), 1.0)

    def get_total_stats(self) -> Dict[str, float]:
        if not self.study_stats:
            return {}
        totals = {name: sum(getattr(s, name) for s in self.study_stats) for name in COUNTER_FIELDS}
        totals["streak_days"] = max(s.streak_days for s in self.study_stats)
        return totals
