import uuid
from django.db import models
from django.conf import settings
from quizzes.models import Quiz, Question, Choice


class QuizAttempt(models.Model):
    attempt_id = models.UUIDField(
        db_column='attempt_id',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column='student',
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    quiz = models.ForeignKey(
        Quiz,
        db_column='quiz',
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    started_at = models.DateTimeField(
        db_column='started_at',
        auto_now_add=True
    )
    completed_at = models.DateTimeField(
        db_column='completed_at',
        null=True,
        blank=True
    )
    score = models.IntegerField(
        db_column='score',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'quiz_attempts'

    def __str__(self):
        return str(self.attempt_id)


class StudentAnswer(models.Model):
    answer_id = models.UUIDField(
        db_column='answer_id',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    attempt = models.ForeignKey(
        QuizAttempt,
        db_column='attempt',
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        db_column='question',
        on_delete=models.CASCADE
    )
    selected_choice = models.ForeignKey(
        Choice,
        db_column='selected_choice',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'student_answers'

    def __str__(self):
        return str(self.answer_id)
