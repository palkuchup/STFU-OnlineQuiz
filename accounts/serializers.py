from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import CustomUser, TeacherProfile, StudentProfile, RegistrationRequest


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT token serializer using school_id instead of username."""
    username_field = 'school_id'

    def validate(self, attrs):
        school_id = attrs.get('school_id')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            school_id=school_id,
            password=password
        )

        if not user:
            raise serializers.ValidationError(
                {'detail': 'Invalid School ID or password.'}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {'detail': 'This account is inactive. Please contact the administrator.'}
            )

        data = super().validate(attrs)
        # Add user info to token response
        data['user'] = {
            'user_id': str(user.user_id),
            'school_id': user.school_id,
            'full_name': user.full_name,
            'role': user.role,
            'role_display': user.get_role_display(),
        }

        # Add grade_level for students
        if user.is_student and hasattr(user, 'student_profile'):
            data['user']['grade_level'] = user.student_profile.grade_level

        # Add subject for teachers
        if user.is_teacher and hasattr(user, 'teacher_profile'):
            data['user']['subject_specialization'] = user.teacher_profile.subject_specialization

        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['school_id'] = user.school_id
        token['full_name'] = user.full_name
        return token


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ['employee_id', 'subject_specialization', 'get_subject_specialization_display']

    get_subject_specialization_display = serializers.SerializerMethodField()

    def get_get_subject_specialization_display(self, obj):
        return obj.get_subject_specialization_display()


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['grade_level', 'section', 'id_photo_front', 'id_photo_back', 'selfie_photo']


class UserSerializer(serializers.ModelSerializer):
    teacher_profile = TeacherProfileSerializer(read_only=True)
    student_profile = StudentProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'user_id', 'school_id', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'created_at', 'teacher_profile', 'student_profile'
        ]
        read_only_fields = ['user_id', 'created_at', 'full_name']


class RegistrationRequestSerializer(serializers.ModelSerializer):
    """For students to submit registration requests."""

    class Meta:
        model = RegistrationRequest
        fields = [
            'request_id', 'school_id', 'first_name', 'last_name',
            'grade_level', 'section', 'temp_password',
            'id_photo_front', 'id_photo_back', 'selfie_photo',
            'status', 'submitted_at'
        ]
        read_only_fields = ['request_id', 'status', 'submitted_at']
        extra_kwargs = {
            'temp_password': {'write_only': True},
            'id_photo_front': {'required': True},
            'id_photo_back': {'required': True},
            'selfie_photo': {'required': True},
        }

    def validate_school_id(self, value):
        if CustomUser.objects.filter(school_id=value).exists():
            raise serializers.ValidationError("An account with this School ID already exists.")
        if RegistrationRequest.objects.filter(school_id=value, status=RegistrationRequest.STATUS_PENDING).exists():
            raise serializers.ValidationError("A pending registration request with this School ID already exists.")
        return value


class RegistrationRequestAdminSerializer(serializers.ModelSerializer):
    """For admin to view and manage registration requests."""
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = RegistrationRequest
        fields = [
            'request_id', 'school_id', 'first_name', 'last_name',
            'grade_level', 'section',
            'id_photo_front', 'id_photo_back', 'selfie_photo',
            'status', 'rejection_reason', 'submitted_at',
            'reviewed_at', 'reviewed_by', 'reviewed_by_name'
        ]
        read_only_fields = ['request_id', 'submitted_at', 'reviewed_at', 'reviewed_by']

    def get_reviewed_by_name(self, obj):
        if obj.reviewed_by:
            return obj.reviewed_by.full_name
        return None
