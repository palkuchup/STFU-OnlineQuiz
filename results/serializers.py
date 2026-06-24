from rest_framework import serializers
from .models import QuizAttempt, StudentAnswer
from quizzes.serializers import QuizListSerializer, QuestionWithAnswersSerializer
from quizzes.models import Question, Choice


class StudentAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    selected_choice_text = serializers.SerializerMethodField()
    is_correct = serializers.BooleanField(read_only=True)
    correct_choice = serializers.SerializerMethodField()

    class Meta:
        model = StudentAnswer
        fields = [
            'answer_id', 'question', 'question_text',
            'selected_choice', 'selected_choice_text',
            'is_correct', 'correct_choice'
        ]

    def get_selected_choice_text(self, obj):
        if obj.selected_choice:
            return obj.selected_choice.text
        return None

    def get_correct_choice(self, obj):
        correct = obj.question.choices.filter(is_correct=True).first()
        if correct:
            return {'choice_id': str(correct.choice_id), 'text': correct.text}
        return None


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    subject_name = serializers.CharField(source='quiz.subject.name', read_only=True)
    grade_level = serializers.IntegerField(source='quiz.subject.grade_level', read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = [
            'attempt_id', 'student', 'student_name', 'quiz', 'quiz_title',
            'subject_name', 'grade_level', 'started_at', 'completed_at',
            'is_completed', 'score', 'total_questions', 'percentage'
        ]

    def get_student_name(self, obj):
        return obj.student.full_name


class AttemptDetailSerializer(serializers.ModelSerializer):
    """Full attempt with all answers and correct answers shown."""
    answers = StudentAnswerSerializer(many=True, read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    subject_name = serializers.CharField(source='quiz.subject.name', read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = [
            'attempt_id', 'student', 'student_name', 'quiz', 'quiz_title',
            'subject_name', 'started_at', 'completed_at', 'is_completed',
            'score', 'total_questions', 'percentage', 'answers'
        ]

    def get_student_name(self, obj):
        return obj.student.full_name


class QuizSubmitSerializer(serializers.Serializer):
    """Accepts a list of {question_id, choice_id} pairs for quiz submission."""
    answers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.UUIDField()
        ),
        min_length=1
    )

    def validate_answers(self, value):
        for item in value:
            if 'question_id' not in item or 'choice_id' not in item:
                raise serializers.ValidationError(
                    "Each answer must have 'question_id' and 'choice_id'."
                )
        return value
