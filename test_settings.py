from FitnessTrackerApp_backend.settings import *

# Use SQLite for testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use a simpler password hasher for tests
AUTH_PASSWORD_VALIDATORS = []

# Disable logging during tests
import logging
logging.disable(logging.CRITICAL)
