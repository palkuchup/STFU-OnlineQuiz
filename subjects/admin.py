from django.contrib import admin
from .models import Subject, Enrollment


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_id', 'name', 'created_by', 'created_at')
    search_fields = ['name', 'created_by__username']
    inlines = [EnrollmentInline]
    list_per_page = 20


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('enrollment_id', 'student', 'subject', 'enrolled_at')
    search_fields = ['student__username', 'subject__name']
    list_per_page = 20


admin.site.register(Subject, SubjectAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
