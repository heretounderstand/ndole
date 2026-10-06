import re
import secrets
import string
from typing import Any, Dict, Optional, Tuple
from model import User, now_iso
from utils.data import get_auth_client, get_db

EMAIL_DOMAIN = "ndole.cm"
SPECIAL_CHARS = "!@#$%^&*(),.?:{}|<>"


def _email(username: str) -> str:
    return f"{username}@{EMAIL_DOMAIN}"


def username_exists(username: str) -> bool:
    response = get_db().table('users').select('username').eq('username', username).limit(1).execute()
    return len(response.data) > 0


def validate_username_format(username: str) -> Tuple[bool, str]:
    if len(username) < 4 or len(username) > 20:
        return False, "The username must be between 4 and 20 characters."
    if not re.fullmatch(r'[a-zA-Z0-9_]+', username):
        return False, "The username can only contain letters, numbers and underscores (_)."
    return True, ""


def validate_username(username: str) -> Tuple[bool, str]:
    valid, message = validate_username_format(username)
    if not valid:
        return valid, message
    if username_exists(username):
        return False, "This username is already taken."
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one capital letter."
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return False, "The password must contain at least one number."
    if not any(c in SPECIAL_CHARS + '"' for c in password):
        return False, "The password must contain at least one special character."
    return True, ""


def generate_username() -> str:
    adjectives = ["Brave", "Clever", "Dynamic", "Eager", "Friendly", "Gentle", "Happy", "Intelligent", "Jovial", "Kind"]
    nouns = ["Explorer", "Scholar", "Pioneer", "Learner", "Thinker", "Reader", "Student", "Innovator", "Champion", "Master"]
    while True:
        username = f"{secrets.choice(adjectives)}{secrets.choice(nouns)}{secrets.randbelow(9999) + 1}"
        if len(username) <= 20 and not username_exists(username):
            return username


def generate_password(length: int = 14) -> str:
    # `secrets`, not `random`: generated passwords must not be predictable.
    pools = [string.ascii_uppercase, string.ascii_lowercase, string.digits, SPECIAL_CHARS]
    password = [secrets.choice(pool) for pool in pools]
    all_chars = "".join(pools)
    password += [secrets.choice(all_chars) for _ in range(length - len(pools))]
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


def register_user(username: str, password: str) -> Tuple[bool, str, Optional[User]]:
    username_valid, username_error = validate_username(username)
    if not username_valid:
        return False, username_error, None
    password_valid, password_error = validate_password(password)
    if not password_valid:
        return False, password_error, None
    try:
        auth_response = get_auth_client().auth.sign_up({
            "email": _email(username),
            "password": password,
        })
        if auth_response.user is None:
            return False, "Registration failed. Please try again.", None
        user = User(user_id=auth_response.user.id, username=username)
        get_db().table('users').insert(user.model_dump()).execute()
        return True, "Registration successful!", user
    except Exception as e:
        if "already registered" in str(e).lower():
            return False, "This username is already taken.", None
        return False, f"Error while registering: {e}", None


def _authenticate(username: str, password: str) -> Optional[str]:
    """Return the auth user id if the credentials are valid."""
    try:
        auth_response = get_auth_client().auth.sign_in_with_password({
            "email": _email(username),
            "password": password,
        })
    except Exception:
        return None
    return auth_response.user.id if auth_response.user else None


def login_user(username: str, password: str) -> Tuple[bool, str, Optional[User]]:
    username = username.strip()
    if not username or not password:
        return False, "Please enter your username and password.", None
    try:
        user_id = _authenticate(username, password)
        if not user_id:
            return False, "Incorrect username or password.", None
        db = get_db()
        user_response = db.table('users').select('*').eq('user_id', user_id).limit(1).execute()
        if not user_response.data:
            return False, "User profile not found.", None
        user_data = user_response.data[0]
        if user_data.get('is_deleted'):
            return False, "This account has been deleted.", None
        current_time = now_iso()
        db.table('users').update({'last_login': current_time}).eq('user_id', user_id).execute()
        user = User.from_row({**user_data, 'last_login': current_time})
        return True, "Connection successful!", user
    except Exception as e:
        return False, f"Error while connecting: {e}", None


def change_password(username: str, current_password: str, new_password: str) -> Tuple[bool, str]:
    valid, message = validate_password(new_password)
    if not valid:
        return False, message
    client = get_auth_client()
    try:
        client.auth.sign_in_with_password({"email": _email(username), "password": current_password})
    except Exception:
        return False, "Your current password is incorrect."
    try:
        client.auth.update_user({"password": new_password})
        return True, "Password updated."
    except Exception as e:
        return False, f"Could not update the password: {e}"
    finally:
        try:
            client.auth.sign_out({"scope": "local"})
        except Exception:
            pass


def generate_credentials() -> Dict[str, str]:
    return {
        "username": generate_username(),
        "password": generate_password()
    }


def check_credentials(username: str, password: str) -> Dict[str, Any]:
    username_valid, username_message = validate_username(username)
    password_valid, password_message = validate_password(password)
    return {
        "username_valid": username_valid,
        "username_message": username_message,
        "password_valid": password_valid,
        "password_message": password_message,
        "all_valid": username_valid and password_valid
    }
