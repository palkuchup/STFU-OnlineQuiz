from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils import timezone
from django.contrib.auth import get_user_model
from subjects.models import Subject, Enrollment
from .models import CustomUser, RegistrationRequest, StudentProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserSerializer,
    RegistrationRequestSerializer,
    RegistrationRequestAdminSerializer,
)
from .permissions import IsAdmin, IsAdminOrReadOwn

User = get_user_model()


class LoginView(TokenObtainPairView):
    """POST /api/auth/login/ — authenticate with school_id + password, return JWT."""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class StudentRegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — student submits registration request with photos."""
    serializer_class = RegistrationRequestSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(
            {
                'message': 'Registration request submitted successfully. Please wait for admin approval.',
                'request_id': str(instance.request_id),
                'status': instance.status,
            },
            status=status.HTTP_201_CREATED
        )


class RegistrationRequestListView(generics.ListAPIView):
    """GET /api/auth/registration-requests/ — admin lists all requests."""
    serializer_class = RegistrationRequestAdminSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = RegistrationRequest.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class RegistrationRequestDetailView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/registration-requests/<id>/ — admin approves or rejects."""
    queryset = RegistrationRequest.objects.all()
    serializer_class = RegistrationRequestAdminSerializer
    permission_classes = [IsAdmin]
    lookup_field = 'request_id'

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('status')
        rejection_reason = request.data.get('rejection_reason', '')

        if instance.status != RegistrationRequest.STATUS_PENDING:
            return Response(
                {'detail': 'This request has already been reviewed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status == RegistrationRequest.STATUS_APPROVED:
            # Create user account
            if User.objects.filter(school_id=instance.school_id).exists():
                return Response(
                    {'detail': 'A user with this School ID already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = User.objects.create_user(
                school_id=instance.school_id,
                username=instance.school_id,
                first_name=instance.first_name,
                last_name=instance.last_name,
                password=instance.temp_password,
                role=User.ROLE_STUDENT,
                is_active=True,
            )

            StudentProfile.objects.create(
                user=user,
                grade_level=instance.grade_level,
                id_photo_front=instance.id_photo_front,
                id_photo_back=instance.id_photo_back,
                selfie_photo=instance.selfie_photo,
                section=instance.section,
            )

            # Auto-enroll in all 4 subjects of their grade level
            subjects = Subject.objects.filter(grade_level=instance.grade_level)
            for subject in subjects:
                Enrollment.objects.get_or_create(student=user, subject=subject)

            instance.status = RegistrationRequest.STATUS_APPROVED

        elif new_status == RegistrationRequest.STATUS_REJECTED:
            instance.status = RegistrationRequest.STATUS_REJECTED
            instance.rejection_reason = rejection_reason
        else:
            return Response(
                {'detail': 'Invalid status. Use "approved" or "rejected".'},
                status=status.HTTP_400_BAD_REQUEST
            )

        instance.reviewed_at = timezone.now()
        instance.reviewed_by = request.user
        instance.save()

        return Response(
            self.get_serializer(instance).data,
            status=status.HTTP_200_OK
        )


class MeView(generics.RetrieveUpdateAPIView):
    """GET /api/auth/me/ — get current user profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    """GET /api/auth/users/ — admin lists all users."""
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = User.objects.all().order_by('-created_at')
        role = self.request.query_params.get('role')
        if role is not None:
            qs = qs.filter(role=role)
        return qs
