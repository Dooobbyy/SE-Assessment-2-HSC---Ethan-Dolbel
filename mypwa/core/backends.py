# core/backends.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in
    using either their username or email address.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate the user based on username or email.
        """
        if username is None:
            # Get username from kwargs if not passed as username (depends on form)
            # The standard AuthenticationForm passes it as 'username'
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        try:
            # Use Q objects to perform an OR query on username and email
            # iexact for case-insensitive matching on email (standard practice)
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce timing difference
            # between existence and non-existence of a user (security best practice)
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # Handle case where username and email are the same for different users (rare)
            # Log this incident, decide policy (e.g., prefer username, reject login, notify admins)
            # For now, just fail authentication
            # Consider logging: import logging; logger = logging.getLogger(__name__); logger.warning(...)
            return None

        # Check the password against the retrieved user
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
