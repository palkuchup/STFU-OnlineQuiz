import uuid
from django.db import models
from django.conf import settings
from quizzes.models import Quiz, Question, Choice


class QuizAttempt(models.Model):
    attempt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    total_questions = models.IntegerField(default=0)
    percentage = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.student} — {self.quiz.title} ({self.score}/{self.total_questions})"

    def compute_score(self):
        """Compute and save the score based on submitted answers."""
        correct = self.answers.filter(selected_choice__is_correct=True).count()
        total = self.quiz.questions.count()
        self.score = correct
        self.total_questions = total
        self.percentage = round((correct / total * 100), 2) if total > 0 else 0.0
        return self.score


class StudentAnswer(models.Model):
    answer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='student_answers'
    )
    selected_choice = models.ForeignKey(
        Choice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='selected_by'
    )

    class Meta:
        db_table = 'student_answers'
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f"Attempt {self.attempt_id} — Q: {self.question_id}"

    @property
    def is_correct(self):
        return self.selected_choice is not None and self.selected_choice.is_correct
