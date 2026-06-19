from django.contrib import admin
from .models import QuizAttempt, StudentAnswer


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 1


class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('attempt_id', 'student', 'quiz', 'started_at', 'completed_at', 'score')
    search_fields = ['student__username', 'quiz__title']
    inlines = [StudentAnswerInline]
    list_per_page = 20


class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('answer_id', 'attempt', 'question', 'selected_choice')
    search_fields = ['attempt__student__username', 'question__text']
    list_per_page = 20


admin.site.register(QuizAttempt, QuizAttemptAdmin)
admin.site.register(StudentAnswer, StudentAnswerAdmin)
