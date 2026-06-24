from django.contrib import admin
from .models import QuizAttempt, StudentAnswer


class StudentAnswerInline(admin.TabularInline):
    model = StudentAnswer
    extra = 0
    readonly_fields = ('question', 'selected_choice', 'is_correct')
    fields = ('question', 'selected_choice', 'is_correct')

    def is_correct(self, obj):
        return obj.is_correct
    is_correct.boolean = True
    is_correct.short_description = 'Correct?'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'total_questions', 'percentage', 'is_completed', 'started_at')
    list_filter = ('is_completed', 'quiz__subject__grade_level', 'quiz__quiz_type')
    search_fields = ('student__school_id', 'student__first_name', 'quiz__title')
    inlines = [StudentAnswerInline]
    readonly_fields = ('started_at', 'completed_at', 'score', 'total_questions', 'percentage')
    list_per_page = 25


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_choice', 'is_correct_display')
    search_fields = ('attempt__student__school_id', 'question__text')
    list_per_page = 25

    def is_correct_display(self, obj):
        return obj.is_correct
    is_correct_display.boolean = True
    is_correct_display.short_description = 'Correct?'
