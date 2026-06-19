import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_ADMIN = 0
    ROLE_TEACHER = 1
    ROLE_STUDENT = 2

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_STUDENT, 'Student'),
    ]

    user_id = models.UUIDField(
        db_column='user_id',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    role = models.IntegerField(
        db_column='role',
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT
    )

    def __str__(self):
        return str(self.user_id)
