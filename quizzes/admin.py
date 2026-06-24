from django.contrib import admin
from .models import Quiz, Question, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    fields = ('text', 'is_correct', 'order')


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ('text', 'order', 'image')
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'quiz_type', 'created_by', 'is_active', 'question_count', 'created_at')
    list_filter = ('quiz_type', 'is_active', 'subject__grade_level', 'subject__subject_code')
    search_fields = ('title', 'subject__name', 'created_by__first_name')
    inlines = [QuestionInline]
    list_per_page = 20
    readonly_fields = ('created_at', 'updated_at')

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = '# Questions'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'quiz', 'order')
    search_fields = ('text', 'quiz__title')
    inlines = [ChoiceInline]
    list_per_page = 20

    def text_preview(self, obj):
        return obj.text[:80]
    text_preview.short_description = 'Question'


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'order')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')
    list_per_page = 25
