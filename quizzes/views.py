from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from accounts.models import CustomUser
from accounts.permissions import IsTeacher, IsAdminOrTeacher
from subjects.models import Enrollment
from .models import Quiz
from .serializers import QuizListSerializer, QuizDetailSerializer, QuizCreateSerializer


class QuizListView(generics.ListAPIView):
    """
    GET /api/quizzes/
    - Student: active quizzes for their enrolled subjects only
    - Teacher: their own quizzes (all statuses)
    - Admin: all quizzes
    """
    serializer_class = QuizListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Quiz.objects.select_related('subject', 'created_by')

        if user.role == CustomUser.ROLE_STUDENT:
            enrolled_subject_ids = Enrollment.objects.filter(
                student=user, is_active=True
            ).values_list('subject_id', flat=True)
            return qs.filter(subject_id__in=enrolled_subject_ids, is_active=True)

        if user.role == CustomUser.ROLE_TEACHER:
            qs = qs.filter(created_by=user)
            quiz_type = self.request.query_params.get('quiz_type')
            if quiz_type:
                qs = qs.filter(quiz_type=quiz_type)
            return qs

        # Admin: all, with optional filters
        quiz_type = self.request.query_params.get('quiz_type')
        subject_id = self.request.query_params.get('subject')
        if quiz_type:
            qs = qs.filter(quiz_type=quiz_type)
        if subject_id:
            qs = qs.filter(subject_id=subject_id)
        return qs


class QuizDetailView(generics.RetrieveAPIView):
    """GET /api/quizzes/<id>/ — full quiz with questions (no correct answers)."""
    serializer_class = QuizDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'quiz_id'

    def get_queryset(self):
        user = self.request.user
        qs = Quiz.objects.prefetch_related('questions__choices')

        if user.role == CustomUser.ROLE_STUDENT:
            enrolled_subject_ids = Enrollment.objects.filter(
                student=user, is_active=True
            ).values_list('subject_id', flat=True)
            return qs.filter(subject_id__in=enrolled_subject_ids, is_active=True)

        if user.role == CustomUser.ROLE_TEACHER:
            return qs.filter(created_by=user)

        return qs  # Admin sees all


class QuizCreateView(generics.CreateAPIView):
    """POST /api/quizzes/ — teacher creates a new quiz with questions."""
    serializer_class = QuizCreateSerializer
    permission_classes = [IsTeacher]


class QuizToggleActiveView(APIView):
    """PATCH /api/quizzes/<id>/toggle-active/ — teacher activates/deactivates quiz."""
    permission_classes = [IsTeacher]

    def patch(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, quiz_id=quiz_id, created_by=request.user)
        quiz.is_active = not quiz.is_active
        quiz.save()
        return Response(
            {
                'quiz_id': str(quiz.quiz_id),
                'title': quiz.title,
                'is_active': quiz.is_active,
                'message': f"Quiz {'activated' if quiz.is_active else 'deactivated'} successfully."
            },
            status=status.HTTP_200_OK
        )


class QuizUpdateView(generics.UpdateAPIView):
    """PATCH /api/quizzes/<id>/edit/ — teacher updates quiz metadata."""
    permission_classes = [IsTeacher]
    lookup_field = 'quiz_id'

    def get_serializer_class(self):
        return QuizCreateSerializer

    def get_queryset(self):
        return Quiz.objects.filter(created_by=self.request.user)


class QuizDeleteView(generics.DestroyAPIView):
    """DELETE /api/quizzes/<id>/delete/ — teacher deletes their quiz."""
    permission_classes = [IsTeacher]
    lookup_field = 'quiz_id'

    def get_queryset(self):
        return Quiz.objects.filter(created_by=self.request.user)
