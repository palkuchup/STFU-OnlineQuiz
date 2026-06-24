from django.contrib import admin
from .models import Subject, Enrollment


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ('enrolled_at', 'is_promoted')
    fields = ('student', 'is_active', 'final_grade', 'is_promoted', 'enrolled_at')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject_code', 'grade_level', 'teacher', 'passing_score', 'created_at')
    list_filter = ('grade_level', 'subject_code')
    search_fields = ('name', 'teacher__first_name', 'teacher__last_name')
    inlines = [EnrollmentInline]
    list_per_page = 20


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'is_active', 'final_grade', 'is_promoted', 'enrolled_at')
    list_filter = ('is_active', 'is_promoted', 'subject__grade_level', 'subject__subject_code')
    search_fields = ('student__school_id', 'student__first_name', 'subject__name')
    readonly_fields = ('enrolled_at', 'final_grade_submitted_at')
    list_per_page = 25
