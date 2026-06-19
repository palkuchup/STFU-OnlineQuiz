import uuid
from django.db import models
from django.conf import settings


class Subject(models.Model):
    subject_id = models.UUIDField(
        db_column='subject_id',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(
        db_column='name',
        max_length=100,
        blank=False
    )
    description = models.TextField(
        db_column='description',
        blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column='created_by',
        on_delete=models.CASCADE,
        related_name='subjects'
    )
    created_at = models.DateTimeField(
        db_column='created_at',
        auto_now_add=True
    )

    def __str__(self):
        return str(self.subject_id)


class Enrollment(models.Model):
    enrollment_id = models.UUIDField(
        db_column='enrollment_id',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column='student',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    subject = models.ForeignKey(
        Subject,
        db_column='subject',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(
        db_column='enrolled_at',
        auto_now_add=True
    )

    class Meta:
        db_table = 'enrollments'
        unique_together = ('student', 'subject')

    def __str__(self):
        return str(self.enrollment_id)
