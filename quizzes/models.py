import uuid
from django.db import models
from django.conf import settings
from subjects.models import Subject


class Quiz(models.Model):
    QUIZ_TYPE_REGULAR = 'regular'
    QUIZ_TYPE_SELF_ASSESSMENT = 'self_assessment'
    QUIZ_TYPE_FINAL_EXAM = 'final_exam'

    QUIZ_TYPE_CHOICES = [
        (QUIZ_TYPE_REGULAR, 'Regular Quiz'),
        (QUIZ_TYPE_SELF_ASSESSMENT, 'Self-Assessment'),
        (QUIZ_TYPE_FINAL_EXAM, 'Final Quiz'),
    ]

    quiz_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='quizzes'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_quizzes'
    )
    quiz_type = models.CharField(
        max_length=20,
        choices=QUIZ_TYPE_CHOICES,
        default=QUIZ_TYPE_REGULAR
    )
    time_limit = models.IntegerField(
        help_text='Time limit in minutes (0 = no limit)',
        default=0
    )
    is_active = models.BooleanField(default=False)
    # Allow multiple attempts for self-assessment
    allow_multiple_attempts = models.BooleanField(default=False)
    # Show correct answers after submission
    show_answers_after_submit = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'quizzes'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_quiz_type_display()})"

    @property
    def question_count(self):
        return self.questions.count()

    @property
    def grade_level(self):
        return self.subject.grade_level


class Question(models.Model):
    question_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    text = models.TextField(blank=False)
    order = models.IntegerField(default=0)
    # Optional image for question
    image = models.ImageField(upload_to='question_images/', null=True, blank=True)

    class Meta:
        db_table = 'questions'
        ordering = ['order']

    def __str__(self):
        return f"Q{self.order}: {self.text[:60]}"


class Choice(models.Model):
    choice_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices'
    )
    text = models.CharField(max_length=500, blank=False)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'choices'
        ordering = ['order']

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:60]}"
