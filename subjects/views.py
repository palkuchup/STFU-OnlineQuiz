from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from accounts.models import CustomUser, StudentProfile
from accounts.permissions import IsAdmin, IsTeacher, IsAdminOrTeacher
from .models import Subject, Enrollment
from .serializers import SubjectSerializer, EnrollmentSerializer, FinalGradeSubmitSerializer


class SubjectListView(generics.ListAPIView):
    """
    GET /api/subjects/
    - Student: subjects for their grade level
    - Teacher: subjects they teach
    - Admin: all subjects
    """
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Subject.objects.select_related('teacher')

        if user.role == CustomUser.ROLE_STUDENT:
            if hasattr(user, 'student_profile'):
                return qs.filter(grade_level=user.student_profile.grade_level)
            return Subject.objects.none()

        if user.role == CustomUser.ROLE_TEACHER:
            return qs.filter(teacher=user)

        # Admin: all subjects, optional filters
        grade = self.request.query_params.get('grade_level')
        subject_code = self.request.query_params.get('subject_code')
        if grade:
            qs = qs.filter(grade_level=grade)
        if subject_code:
            qs = qs.filter(subject_code=subject_code)
        return qs


class SubjectDetailView(generics.RetrieveAPIView):
    """GET /api/subjects/<id>/"""
    queryset = Subject.objects.select_related('teacher')
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'subject_id'


class EnrollmentListView(generics.ListAPIView):
    """
    GET /api/subjects/enrollments/
    - Student: their own enrollments
    - Teacher: enrollments for their subjects
    - Admin: all enrollments
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Enrollment.objects.select_related('student', 'subject')

        if user.role == CustomUser.ROLE_STUDENT:
            return qs.filter(student=user)
        if user.role == CustomUser.ROLE_TEACHER:
            return qs.filter(subject__teacher=user)
        return qs  # Admin sees all


class SubmitFinalGradeView(APIView):
    """
    POST /api/subjects/final-grade/
    Teacher submits a student's final grade.
    If grade >= subject.passing_score, auto-enrolls student in same subject at next grade level.
    """
    permission_classes = [IsTeacher]

    def post(self, request, *args, **kwargs):
        serializer = FinalGradeSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        student_id = serializer.validated_data['student_id']
        subject_id = serializer.validated_data['subject_id']
        final_grade = serializer.validated_data['final_grade']

        subject = get_object_or_404(Subject, subject_id=subject_id, teacher=request.user)
        student = get_object_or_404(CustomUser, user_id=student_id, role=CustomUser.ROLE_STUDENT)

        enrollment = get_object_or_404(Enrollment, student=student, subject=subject)

        if enrollment.final_grade is not None:
            return Response(
                {'detail': 'Final grade has already been submitted for this enrollment.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment.final_grade = final_grade
        enrollment.final_grade_submitted_at = timezone.now()

        # Check if student passes and should be promoted
        if final_grade >= subject.passing_score:
            enrollment.is_promoted = True
            next_grade = subject.grade_level + 1

            if next_grade <= 10:
                next_subject = Subject.objects.filter(
                    subject_code=subject.subject_code,
                    grade_level=next_grade
                ).first()

                if next_subject:
                    Enrollment.objects.get_or_create(student=student, subject=next_subject)

                    # Also update student's grade level if ALL 4 subjects are promoted
                    all_current_enrollments = Enrollment.objects.filter(
                        student=student,
                        subject__grade_level=subject.grade_level
                    )
                    if all_current_enrollments.filter(is_promoted=True).count() == 4:
                        profile = student.student_profile
                        profile.grade_level = next_grade
                        profile.save()

        enrollment.save()

        return Response(
            {
                'message': f'Final grade of {final_grade} submitted for {student.full_name}.',
                'promoted': enrollment.is_promoted,
                'next_grade': subject.grade_level + 1 if enrollment.is_promoted and subject.grade_level < 10 else None,
            },
            status=status.HTTP_200_OK
        )
