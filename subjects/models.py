import uuid
from django.db import models
from django.conf import settings


class Subject(models.Model):
    SUBJECT_ENGLISH = 'english'
    SUBJECT_MATH = 'math'
    SUBJECT_SCIENCE = 'science'
    SUBJECT_FILIPINO = 'filipino'

    SUBJECT_CODE_CHOICES = [
        (SUBJECT_ENGLISH, 'English'),
        (SUBJECT_MATH, 'Math'),
        (SUBJECT_SCIENCE, 'Science'),
        (SUBJECT_FILIPINO, 'Filipino'),
    ]

    GRADE_CHOICES = [
        (7, 'Grade 7'),
        (8, 'Grade 8'),
        (9, 'Grade 9'),
        (10, 'Grade 10'),
    ]

    subject_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject_code = models.CharField(
        max_length=20,
        choices=SUBJECT_CODE_CHOICES,
        help_text='Subject category'
    )
    grade_level = models.IntegerField(
        choices=GRADE_CHOICES,
        help_text='Grade level for this subject'
    )
    name = models.CharField(
        max_length=200,
        help_text='Full display name e.g. "English - Grade 7"'
    )
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_subjects',
        limit_choices_to={'role': 1}  # ROLE_TEACHER
    )
    passing_score = models.IntegerField(
        default=50,
        help_text='Minimum score (0-100) required to advance to next grade level'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subjects'
        unique_together = ('subject_code', 'grade_level')
        ordering = ['grade_level', 'subject_code']

    def __str__(self):
        return self.name


class Enrollment(models.Model):
    enrollment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 2}  # ROLE_STUDENT
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    # Set when teacher submits final grade and student passes
    final_grade = models.FloatField(null=True, blank=True)
    final_grade_submitted_at = models.DateTimeField(null=True, blank=True)
    is_promoted = models.BooleanField(
        default=False,
        help_text='True when student passed and was promoted to next grade level'
    )

    class Meta:
        db_table = 'enrollments'
        unique_together = ('student', 'subject')
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student} → {self.subject}"
