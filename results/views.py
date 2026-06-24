from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from accounts.models import CustomUser
from accounts.permissions import IsStudent, IsTeacher, IsAdminOrTeacher
from subjects.models import Enrollment
from quizzes.models import Quiz, Question, Choice
from .models import QuizAttempt, StudentAnswer
from .serializers import QuizAttemptSerializer, AttemptDetailSerializer, QuizSubmitSerializer


class StartAttemptView(APIView):
    """POST /api/results/quizzes/<quiz_id>/start/ — student starts a quiz attempt."""
    permission_classes = [IsStudent]

    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, quiz_id=quiz_id, is_active=True)

        # Verify student is enrolled in this subject
        is_enrolled = Enrollment.objects.filter(
            student=request.user,
            subject=quiz.subject,
            is_active=True
        ).exists()
        if not is_enrolled:
            return Response(
                {'detail': 'You are not enrolled in this subject.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check multiple attempts
        existing_attempts = QuizAttempt.objects.filter(
            student=request.user,
            quiz=quiz,
            is_completed=True
        )
        if existing_attempts.exists() and not quiz.allow_multiple_attempts:
            return Response(
                {'detail': 'You have already completed this quiz.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for incomplete attempt already in progress
        incomplete = QuizAttempt.objects.filter(
            student=request.user,
            quiz=quiz,
            is_completed=False
        ).first()
        if incomplete:
            return Response(
                AttemptDetailSerializer(incomplete).data,
                status=status.HTTP_200_OK
            )

        # Create new attempt
        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            total_questions=quiz.questions.count()
        )

        return Response(
            {
                'attempt_id': str(attempt.attempt_id),
                'quiz_id': str(quiz.quiz_id),
                'quiz_title': quiz.title,
                'time_limit': quiz.time_limit,
                'total_questions': attempt.total_questions,
                'started_at': attempt.started_at,
            },
            status=status.HTTP_201_CREATED
        )


class SubmitAttemptView(APIView):
    """POST /api/results/attempts/<attempt_id>/submit/ — student submits answers."""
    permission_classes = [IsStudent]

    def post(self, request, attempt_id):
        attempt = get_object_or_404(
            QuizAttempt,
            attempt_id=attempt_id,
            student=request.user,
            is_completed=False
        )

        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers_data = serializer.validated_data['answers']

        # Save each answer
        for ans in answers_data:
            question = get_object_or_404(Question, question_id=ans['question_id'], quiz=attempt.quiz)
            choice = get_object_or_404(Choice, choice_id=ans['choice_id'], question=question)

            StudentAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={'selected_choice': choice}
            )

        # Compute and save score
        attempt.compute_score()
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()

        response_data = {
            'attempt_id': str(attempt.attempt_id),
            'score': attempt.score,
            'total_questions': attempt.total_questions,
            'percentage': attempt.percentage,
            'completed_at': attempt.completed_at,
        }

        # Include answers with correct flag if quiz allows it
        if attempt.quiz.show_answers_after_submit:
            response_data['results'] = AttemptDetailSerializer(attempt).data

        return Response(response_data, status=status.HTTP_200_OK)


class AttemptDetailView(generics.RetrieveAPIView):
    """GET /api/results/attempts/<attempt_id>/ — review a completed attempt."""
    serializer_class = AttemptDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'attempt_id'

    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.ROLE_STUDENT:
            return QuizAttempt.objects.filter(student=user, is_completed=True)
        if user.role == CustomUser.ROLE_TEACHER:
            return QuizAttempt.objects.filter(quiz__created_by=user, is_completed=True)
        return QuizAttempt.objects.filter(is_completed=True)


class StudentHistoryView(generics.ListAPIView):
    """GET /api/results/history/ — student's quiz attempt history."""
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return QuizAttempt.objects.filter(
            student=self.request.user,
            is_completed=True
        ).select_related('quiz__subject').order_by('-completed_at')


class TeacherResultsView(generics.ListAPIView):
    """GET /api/results/quiz/<quiz_id>/results/ — teacher views all student attempts for their quiz."""
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        quiz_id = self.kwargs.get('quiz_id')
        quiz = get_object_or_404(Quiz, quiz_id=quiz_id, created_by=self.request.user)
        return QuizAttempt.objects.filter(
            quiz=quiz,
            is_completed=True
        ).select_related('student').order_by('-completed_at')


class TeacherSubjectResultsView(generics.ListAPIView):
    """GET /api/results/subject/<subject_id>/results/ — teacher views results for all quizzes in a subject."""
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        subject_id = self.kwargs.get('subject_id')
        return QuizAttempt.objects.filter(
            quiz__subject_id=subject_id,
            quiz__created_by=self.request.user,
            is_completed=True
        ).select_related('student', 'quiz').order_by('-completed_at')
