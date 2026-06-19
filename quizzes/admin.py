from django.contrib import admin
from .models import Quiz, Question, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    inlines = [ChoiceInline]


class QuizAdmin(admin.ModelAdmin):
    list_display = ('quiz_id', 'title', 'subject', 'created_by', 'is_active', 'created_at')
    search_fields = ['title', 'subject__name', 'created_by__username']
    inlines = [QuestionInline]
    list_per_page = 20


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_id', 'quiz', 'text', 'order')
    search_fields = ['text', 'quiz__title']
    inlines = [ChoiceInline]
    list_per_page = 20


class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('choice_id', 'question', 'text', 'is_correct')
    search_fields = ['text', 'question__text']
    list_per_page = 20


admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
