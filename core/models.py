import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    fullname = models.CharField(max_length=100, blank=False, null=False)
    email = models.EmailField(max_length=254, unique=True, blank=False, null=False)
    balance = models.IntegerField(default=1500)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'fullname']

    def __str__(self):
        return self.username
