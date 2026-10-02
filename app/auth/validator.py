import re

def check_password_strength(password: str) -> bool:
    """
    Checks if the password meets the requirements (length, complexity, etc.).
    Returns True if the password is strong enough, False otherwise.
    """
    # Example requirements: at least 8 characters, contains uppercase, lowercase, digit, and special character
    if len(password) < 8:
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char.islower() for char in password):
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for char in password):
        return False
    return True

def is_valid_email(email: str) -> bool:
    """
    Checks if the email is in a proper format.
    Returns True if the email is valid, False otherwise.
    """

    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None