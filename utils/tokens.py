from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
    
    
def get_id_token(user: User):
    """ Return the id and token of a user.

    Args:
        user (User): user to get the id and token from
    """
    
    token_manager = PasswordResetTokenGenerator()
    token = token_manager.make_token(user)
    return f"{user.id}-{token}"


def validate_user_token(user_id: int, token: str,
                        filter_active: bool = True) -> tuple[bool, User]:
    """ Validate user_id and token from url

    Args:
        user_id (int): id of the user to reset password
        token (str): django token to validate
        filter_active (bool): filter active users only

    Returns:
        tuple[bool, User]:
            bool: True if user and token are valid, False otherwise
            User: user object
    """
    
    user = User.objects.filter(id=user_id, is_active=filter_active)
    
    # render error message if user does not exist
    if not user.exists():
        return False, user
        
    user = user[0]
    
    # Validate token
    token_manager = PasswordResetTokenGenerator()
    is_valid = token_manager.check_token(user, token)
    
    # render error message if token is invalid
    if not is_valid:
        return False, user
    
    return True, user