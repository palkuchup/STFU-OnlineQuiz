import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_ADMIN = 0
    ROLE_TEACHER = 1
    ROLE_STUDENT = 2

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_TEACHER, 'Teacher'),
        (ROLE_STUDENT, 'Student'),
    ]

    user_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # School ID used as the login username
    school_id = models.CharField(
        max_length=20,
        unique=True,
        help_text='School-issued ID number (used to log in)'
    )
    role = models.IntegerField(
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT
    )
    first_name = models.CharField(max_length=100, blank=False)
    last_name = models.CharField(max_length=100, blank=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Use school_id as the login field
    USERNAME_FIELD = 'school_id'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', 'role']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.school_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_teacher(self):
        return self.role == self.ROLE_TEACHER

    @property
    def is_student(self):
        return self.role == self.ROLE_STUDENT


class TeacherProfile(models.Model):
    SUBJECT_ENGLISH = 'english'
    SUBJECT_MATH = 'math'
    SUBJECT_SCIENCE = 'science'
    SUBJECT_FILIPINO = 'filipino'

    SUBJECT_CHOICES = [
        (SUBJECT_ENGLISH, 'English'),
        (SUBJECT_MATH, 'Math'),
        (SUBJECT_SCIENCE, 'Science'),
        (SUBJECT_FILIPINO, 'Filipino'),
    ]

    profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )
    employee_id = models.CharField(max_length=20, unique=True)
    subject_specialization = models.CharField(
        max_length=20,
        choices=SUBJECT_CHOICES,
        help_text='Subject this teacher handles (Grades 7-10)'
    )

    class Meta:
        db_table = 'teacher_profiles'

    def __str__(self):
        return f"{self.user.full_name} — {self.get_subject_specialization_display()}"


class StudentProfile(models.Model):
    GRADE_CHOICES = [
        (7, 'Grade 7'),
        (8, 'Grade 8'),
        (9, 'Grade 9'),
        (10, 'Grade 10'),
    ]

    profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    grade_level = models.IntegerField(choices=GRADE_CHOICES)
    id_photo_front = models.ImageField(
        upload_to='student_ids/front/',
        null=True,
        blank=True
    )
    id_photo_back = models.ImageField(
        upload_to='student_ids/back/',
        null=True,
        blank=True
    )
    selfie_photo = models.ImageField(
        upload_to='student_ids/selfie/',
        null=True,
        blank=True
    )
    section = models.CharField(max_length=50, blank=True, default='')
    is_self_registered = models.BooleanField(
        default=False,
        help_text='Indicates if the student registered via the mobile app.'
    )

    class Meta:
        db_table = 'student_profiles'

    def __str__(self):
        return f"{self.user.full_name} — Grade {self.grade_level}"


class RegistrationRequest(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    GRADE_CHOICES = [
        (7, 'Grade 7'),
        (8, 'Grade 8'),
        (9, 'Grade 9'),
        (10, 'Grade 10'),
    ]

    request_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100, null=True, blank=True, default='')
    last_name = models.CharField(max_length=100, null=True, blank=True, default='')
    grade_level = models.IntegerField(choices=GRADE_CHOICES, null=True, blank=True)
    section = models.CharField(max_length=50, blank=True, default='')
    # Temporary password hash stored until approval
    temp_password = models.CharField(max_length=128)
    id_photo_front = models.ImageField(upload_to='registration_requests/front/', null=True, blank=True)
    id_photo_back = models.ImageField(upload_to='registration_requests/back/', null=True, blank=True)
    selfie_photo = models.ImageField(upload_to='registration_requests/selfie/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True, default='')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests'
    )

    class Meta:
        db_table = 'registration_requests'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Request: {self.school_id} ({self.status})"


# ── Proxy Models for Django Admin ─────────────────────────────────────────────

class AdminUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Admin'
        verbose_name_plural = 'Admins'


class TeacherUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'


class StudentUser(CustomUser):
    class Meta:
        proxy = True
        verbose_name = 'Student'
        verbose_name_plural = 'Students'
