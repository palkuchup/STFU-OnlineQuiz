import uuid
from django.db import models
from django.conf import settings
from subjects.models import Subject


class Quiz(models.Model):
    quiz_id = models.UUIDField(
        db_column='quiz_id',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    title = models.CharField(
        db_column='title',
        max_length=200,
        blank=False
    )
    description = models.TextField(
        db_column='description',
        blank=True
    )
    subject = models.ForeignKey(
        Subject,
        db_column='subject',
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        db_column='created_by',
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    time_limit = models.IntegerField(
        db_column='time_limit',
        help_text='Time limit in minutes',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        db_column='is_active',
        default=False
    )
    created_at = models.DateTimeField(
        db_column='created_at',
        auto_now_add=True
    )

    def __str__(self):
        return str(self.quiz_id)


class Question(models.Model):
    question_id = models.UUIDField(
        db_column='question_id',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    quiz = models.ForeignKey(
        Quiz,
        db_column='quiz',
        on_delete=models.CASCADE,
        related_name='questions'
    )
    text = models.TextField(
        db_column='text',
        blank=False
    )
    order = models.IntegerField(
        db_column='order',
        default=0
    )

    class Meta:
        db_table = 'questions'
        ordering = ['order']

    def __str__(self):
        return str(self.question_id)


class Choice(models.Model):
    choice_id = models.UUIDField(
        db_column='choice_id',
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    question = models.ForeignKey(
        Question,
        db_column='question',
        on_delete=models.CASCADE,
        related_name='choices'
    )
    text = models.CharField(
        db_column='text',
        max_length=200,
        blank=False
    )
    is_correct = models.BooleanField(
        db_column='is_correct',
        default=False
    )

    class Meta:
        db_table = 'choices'

    def __str__(self):
        return str(self.choice_id)
