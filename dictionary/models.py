# dictionary/models.py

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings


# Custom user manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError("Users must have an email")
        user = self.model(email=self.normalize_email(email), name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(email, name, password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


# Custom user model
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email



import json
from django.db import models
from django.conf import settings # Use settings for AUTH_USER_MODEL

# Corrected Word model
# your_app/models.py

import json
from django.db import models
from django.conf import settings

# your_app/models.py

import json
from django.db import models
from django.conf import settings

class Word(models.Model):
    word = models.CharField(max_length=255, unique=True)
    all_meanings = models.TextField(null=True, blank=True)
    pronunciation = models.URLField(max_length=500, null=True, blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)

    def __str__(self):
        return self.word

    def _get_data(self):
        """A private helper method to safely load and return the JSON data."""
        if self.all_meanings:
            try:
                return json.loads(self.all_meanings)
            except json.JSONDecodeError:
                return {}
        return {}

    def get_summary(self):
        """Returns the summary string from the JSON data."""
        data = self._get_data()
        return data.get('summary', 'No summary available.')

    def get_meanings(self):
        """Correctly returns only the list of meaning dictionaries."""
        data = self._get_data()
        # This is the critical line that fixes the problem
        return data.get('meanings', [])

    def get_synonyms(self):
        """Returns the list of synonyms."""
        data = self._get_data()
        return data.get('synonyms', [])

    def get_antonyms(self):
        """Returns the list of antonyms."""
        data = self._get_data()
        return data.get('antonyms', [])
    def is_bookmarked_by(self, user):
        """Checks if the word is bookmarked by a specific user."""
        if user.is_authenticated:
            # Assumes your Bookmark model has a 'word' foreign key
            return self.bookmark_set.filter(user=user).exists()
        return False
# History model (unchanged, but included for completeness)
class History(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.word.word}"


# Bookmark model (unchanged, but included for completeness)
class Bookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    bookmarked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.word.word}"