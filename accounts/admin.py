from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.contrib import messages
from .models import (
    CustomUser, TeacherProfile, StudentProfile, RegistrationRequest,
    AdminUser, TeacherUser, StudentUser
)
from subjects.models import Enrollment, Subject


class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False
    verbose_name_plural = 'Teacher Profile'
    extra = 0


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'
    extra = 0


from django import forms

class PreRegisteredUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('school_id', 'first_name', 'last_name', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.school_id
        user.set_unusable_password()
        if commit:
            user.save()
        return user


# Base admin for the proxy models
class BaseRoleUserAdmin(UserAdmin):
    ordering = ('-created_at',)
    list_per_page = 25

    fieldsets = (
        (None, {'fields': ('school_id', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important Dates', {'fields': ('last_login',)}),
    )
    
    add_form = PreRegisteredUserForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('school_id', 'first_name', 'last_name', 'role'),
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'


@admin.register(AdminUser)
class AdminUserAdmin(BaseRoleUserAdmin):
    list_display = ('school_id', 'full_name', 'is_active', 'created_at')
    search_fields = ('school_id', 'first_name', 'last_name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=CustomUser.ROLE_ADMIN)


@admin.register(TeacherUser)
class TeacherUserAdmin(BaseRoleUserAdmin):
    list_display = ('school_id', 'full_name', 'is_active', 'created_at')
    search_fields = ('school_id', 'first_name', 'last_name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=CustomUser.ROLE_TEACHER)

    def get_inline_instances(self, request, obj=None):
        return [TeacherProfileInline(self.model, self.admin_site)]


@admin.register(StudentUser)
class StudentUserAdmin(BaseRoleUserAdmin):
    list_display = ('school_id', 'full_name', 'get_is_self_registered', 'is_active', 'created_at')
    search_fields = ('school_id', 'first_name', 'last_name')
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=CustomUser.ROLE_STUDENT)

    def get_inline_instances(self, request, obj=None):
        return [StudentProfileInline(self.model, self.admin_site)]

    def get_is_self_registered(self, obj):
        if hasattr(obj, 'student_profile'):
            return obj.student_profile.is_self_registered
        return False
    get_is_self_registered.short_description = 'Self Registered'
    get_is_self_registered.boolean = True


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = ('school_id', 'full_name', 'grade_level', 'status', 'submitted_at', 'reviewed_at')
    list_filter = ('status', 'grade_level')
    search_fields = ('school_id', 'first_name', 'last_name')
    ordering = ('-submitted_at',)
    list_per_page = 25
    readonly_fields = ('submitted_at', 'reviewed_at', 'reviewed_by', 'request_id')
    actions = ['approve_requests', 'reject_requests']

    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'

    def approve_requests(self, request, queryset):
        approved_count = 0
        for reg in queryset.filter(status=RegistrationRequest.STATUS_PENDING):
            # Fetch the pre-registered user account
            user = CustomUser.objects.filter(school_id=reg.school_id).first()
            if not user:
                self.message_user(request, f"School ID {reg.school_id} not found in pre-registered list.", messages.WARNING)
                continue

            if user.has_usable_password():
                self.message_user(request, f"School ID {reg.school_id} is already fully registered.", messages.WARNING)
                continue

            # Set the raw password (temp_password is stored as plain text from registration)
            user.set_password(reg.temp_password)
            user.is_active = True
            user.save()

            # Create StudentProfile
            StudentProfile.objects.create(
                user=user,
                grade_level=reg.grade_level,
                id_photo_front=reg.id_photo_front,
                id_photo_back=reg.id_photo_back,
                selfie_photo=reg.selfie_photo,
                section=reg.section,
                is_self_registered=True, # Mark as self-registered via app
            )

            # Auto-enroll in all 4 subjects of their grade level
            if reg.grade_level:
                subjects = Subject.objects.filter(grade_level=reg.grade_level)
                for subject in subjects:
                    Enrollment.objects.get_or_create(student=user, subject=subject)

            # Mark request as approved
            reg.status = RegistrationRequest.STATUS_APPROVED
            reg.reviewed_at = timezone.now()
            reg.reviewed_by = request.user
            reg.save()
            approved_count += 1

        self.message_user(request, f"{approved_count} registration(s) approved successfully.")
    approve_requests.short_description = "✅ Approve selected registration requests"

    def reject_requests(self, request, queryset):
        count = queryset.filter(status=RegistrationRequest.STATUS_PENDING).update(
            status=RegistrationRequest.STATUS_REJECTED,
            reviewed_at=timezone.now(),
            reviewed_by=request.user,
        )
        self.message_user(request, f"{count} registration(s) rejected.")
    reject_requests.short_description = "❌ Reject selected registration requests"
