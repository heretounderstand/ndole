import random
import string
import re
import streamlit as st
from datetime import datetime
from typing import Optional, Tuple, Dict
from model import User, LearningPreference
from cryptography.fernet import Fernet

from utils.data import initialize_supabase, controller

db = initialize_supabase()

def username_exists(username: str) -> bool:
    """Vérifie si un nom d'utilisateur existe déjà dans Supabase"""
    
    # Vérifier dans la table users de Supabase
    response = db.table('users').select('username').eq('username', username).limit(1).execute()
    
    # Vérifier si des résultats ont été trouvés dans la table users
    if len(response.data) > 0:
        return True
    
    return False

def validate_username(username: str) -> Tuple[bool, str]:
    """
    Valide un nom d'utilisateur selon certaines règles
    Retourne (est_valide, message_erreur)
    """
    # Le nom d'utilisateur doit avoir entre 4 et 20 caractères
    if len(username) < 4 or len(username) > 20:
        return False, "The username must be between 4 and 20 characters."
    
    # Le nom d'utilisateur ne doit contenir que des lettres, chiffres et underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "The username can only contain letters, numbers and underscores (_)."
    
    # Vérifier si le nom d'utilisateur existe déjà
    if username_exists(username):
        return False, "This username is already taken."
    
    return True, ""

def validate_password(password: str) -> Tuple[bool, str]:
    """
    Valide un mot de passe selon certaines règles de sécurité
    Retourne (est_valide, message_erreur)
    """
    # Le mot de passe doit avoir au moins 8 caractères
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."
    
    # Le mot de passe doit contenir au moins une lettre majuscule
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one capital letter."
    
    # Le mot de passe doit contenir au moins une lettre minuscule
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    
    # Le mot de passe doit contenir au moins un chiffre
    if not any(c.isdigit() for c in password):
        return False, "The password must contain at least one number."
    
    # Le mot de passe doit contenir au moins un caractère spécial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "The password must contain at least one special character."
    
    return True, ""

def generate_username() -> str:
    """Génère un nom d'utilisateur unique et valide"""
    adjectives = ["Brave", "Clever", "Dynamic", "Eager", "Friendly", "Gentle", "Happy", "Intelligent", "Jovial", "Kind"]
    nouns = ["Explorer", "Scholar", "Pioneer", "Learner", "Thinker", "Reader", "Student", "Innovator", "Champion", "Master"]
    
    while True:
        # Générer un nom d'utilisateur aléatoire en combinant un adjectif, un nom et un nombre
        username = f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(1, 999)}"
        
        # Vérifier si ce nom d'utilisateur est disponible
        if not username_exists(username):
            return username

def generate_password(length: int = 12) -> str:
    """Génère un mot de passe fort et aléatoire"""
    # Ensemble de caractères pour générer un mot de passe fort
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special = "!@#$%^&*(),.?:{}|<>"
    
    # S'assurer que le mot de passe contient au moins un caractère de chaque catégorie
    password = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits),
        random.choice(special)
    ]
    
    # Compléter le reste du mot de passe
    all_chars = uppercase + lowercase + digits + special
    for _ in range(length - 4):
        password.append(random.choice(all_chars))
    
    # Mélanger les caractères pour éviter un motif prévisible
    random.shuffle(password)
    
    return ''.join(password)

def register_user(username: str, password: str) -> Tuple[bool, str, Optional[User]]:
    """
    Enregistre un nouvel utilisateur dans Firebase Auth et Firestore
    Retourne (succès, message, user_object)
    """
    # Valider le nom d'utilisateur
    username_valid, username_error = validate_username(username)
    if not username_valid:
        return False, username_error, None
    
    # Valider le mot de passe
    password_valid, password_error = validate_password(password)
    if not password_valid:
        return False, password_error, None
    
    try:
        # Créer un email basé sur le nom d'utilisateur
        email = f"{username}@ndole.cm"

        # Créer l'utilisateur dans Supabase Auth
        auth_response = db.auth.sign_up({
            "email": email,
            "password": password,
        })

        user_id = auth_response.user.id

        # Créer un objet User
        user = User(
            user_id=user_id,
            username=username
        )

        # Convertir l'objet User en dictionnaire pour la base de données Supabase
        user_data = user.dict()

        # Stocker les informations dans la table users de Supabase
        db.table('users').insert(user_data).execute()

        return True, "Registration successful!", user

    except Exception as e:
    # Vérifier si l'erreur est liée à un email déjà existant
        if "email already registered" in str(e).lower():
            return False, "Error while registering: This email already exists.", None
        else:
            return False, f"Error while registering: {str(e)}", None
    except Exception as e:
        return False, f"Error during registration: {str(e)}", None

def login_user(username: str, password: str) -> Tuple[bool, str, Optional[User]]:
    """
    Authentifie un utilisateur avec Supabase Auth
    Retourne (succès, message, user_object)
    """
    try:
        # Convertir le nom d'utilisateur en email
        email = f"{username}@ndole.cm"
        
        try:
            # Vérifier si l'utilisateur existe dans Supabase
            # Comme nous utilisons l'API côté serveur, nous ne pouvons pas vraiment "authentifier"
            # Mais nous pouvons vérifier si l'utilisateur existe et récupérer ses données
            
            # Chercher l'utilisateur dans la table auth.users
            auth_response = db.auth.sign_in_with_password(
                {
                    "email": email, 
                    "password": password,
                }
            )
            
            if auth_response.user == None:
                return False, "Incorrect username or password.", None
                
            # Récupérer l'ID utilisateur
            user_id = auth_response.user.id
            
            # Load the key from secrets.toml
            key = st.secrets["encryption"]["key"]

            # Use the key for encryption
            cipher = Fernet(key.encode())

            # Encrypt a string (must be bytes)
            encrypted_user_id = cipher.encrypt(user_id.encode())
            
            controller.set('user_id', encrypted_user_id, max_age=60*60*24*30)  # 30 jours
            
            # Mettre à jour la date de dernière connexion
            current_time = datetime.now().isoformat()
            
            # Récupérer les données utilisateur depuis la table users
            user_response = db.table('users').select('*').eq('user_id', user_id).limit(1).execute()
            
            if len(user_response.data) == 0:
                return False, "User profile not found.", None
                
            user_data = user_response.data[0]
            
            # Mettre à jour la date de dernière connexion
            db.table('users').update({'last_login': current_time}).eq('user_id', user_id).execute()
            
            # Créer l'objet User
            user = User(
                user_id=user_id,
                username=username,
                created_at=user_data.get('created_at'),
                last_login=current_time,
                learning_preferences=LearningPreference(**user_data.get('learning_preferences')) if user_data.get('learning_preferences') else LearningPreference(),
                document_accessed=user_data.get('document_accessed',[]),
                liked_documents=user_data.get('liked_documents', []),
                disliked_documents=user_data.get('disliked_documents', []),
                bookmarked_documents=user_data.get('bookmarked_documents', []),
                shared_documents=user_data.get('shared_documents', []),
                experience_points=user_data.get('experience_points', 0),
                level=user_data.get('level', 1),
                profile_picture=user_data.get('profile_picture', ""),
                telegram_id=user_data.get('telegram_id'),
                repositories=user_data.get('repositories', []),
                chat_histories=user_data.get('chat_histories', []),
                badges=user_data.get('badges', []),
                daily_challenges=user_data.get('daily_challenges', {}),
                study_stats=user_data.get('study_stats', []),
                followers=user_data.get('followers', []),
                following=user_data.get('following', []),
                is_deleted=user_data.get('is_deleted', False),
                notification_preferences=user_data.get('notification_preferences', {
                    "study_reminders": True,
                    "new_content": True,
                    "achievement_alerts": True,
                    "challenge_reminders": True,
                })
            )
            
            return True, "Connection successful!", user
            
        except Exception as e:
            return False, f"Error checking user: {str(e)}", None
            
    except Exception as e:
        return False, f"Error while connecting: {str(e)}", None

def generate_credentials() -> Dict[str, str]:
    """Génère un nom d'utilisateur et un mot de passe valides"""
    username = generate_username()
    password = generate_password()
    return {
        "username": username,
        "password": password
    }

def check_credentials(username: str, password: str) -> Dict[str, any]:
    """
    Vérifie si les identifiants fournis sont valides sans créer d'utilisateur
    Retourne un dictionnaire avec les résultats de validation
    """
    username_valid, username_message = validate_username(username)
    password_valid, password_message = validate_password(password)
    
    return {
        "username_valid": username_valid,
        "username_message": username_message,
        "password_valid": password_valid,
        "password_message": password_message,
        "all_valid": username_valid and password_valid
    }
