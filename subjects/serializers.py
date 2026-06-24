from rest_framework import serializers
from .models import Subject, Enrollment
from accounts.serializers import UserSerializer


class SubjectSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    subject_code_display = serializers.SerializerMethodField()
    grade_level_display = serializers.SerializerMethodField()
    quiz_count = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'subject_id', 'subject_code', 'subject_code_display',
            'grade_level', 'grade_level_display', 'name', 'description',
            'teacher', 'teacher_name', 'passing_score', 'quiz_count', 'created_at'
        ]
        read_only_fields = ['subject_id', 'created_at']

    def get_teacher_name(self, obj):
        if obj.teacher:
            return obj.teacher.full_name
        return None

    def get_subject_code_display(self, obj):
        return obj.get_subject_code_display()

    def get_grade_level_display(self, obj):
        return obj.get_grade_level_display()

    def get_quiz_count(self, obj):
        return obj.quizzes.filter(is_active=True).count()


class EnrollmentSerializer(serializers.ModelSerializer):
    subject_detail = SubjectSerializer(source='subject', read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            'enrollment_id', 'student', 'student_name', 'subject',
            'subject_detail', 'is_active', 'final_grade', 'is_promoted',
            'enrolled_at', 'final_grade_submitted_at'
        ]
        read_only_fields = ['enrollment_id', 'enrolled_at', 'is_promoted', 'final_grade_submitted_at']

    def get_student_name(self, obj):
        return obj.student.full_name


class FinalGradeSubmitSerializer(serializers.Serializer):
    """For teacher to submit a student's final grade."""
    student_id = serializers.UUIDField()
    subject_id = serializers.UUIDField()
    final_grade = serializers.FloatField(min_value=0, max_value=100)
