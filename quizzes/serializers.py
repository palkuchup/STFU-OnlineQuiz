from rest_framework import serializers
from .models import Quiz, Question, Choice


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['choice_id', 'text', 'order']
        # NOTE: is_correct is NOT included here to avoid leaking answers during quiz


class ChoiceWithAnswerSerializer(serializers.ModelSerializer):
    """Used when showing results — includes is_correct."""
    class Meta:
        model = Choice
        fields = ['choice_id', 'text', 'is_correct', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['question_id', 'text', 'order', 'image', 'choices']


class QuestionWithAnswersSerializer(serializers.ModelSerializer):
    """Used in results view — choices include is_correct."""
    choices = ChoiceWithAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['question_id', 'text', 'order', 'image', 'choices']


class QuizListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing quizzes."""
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_level = serializers.IntegerField(source='subject.grade_level', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'quiz_id', 'title', 'description', 'quiz_type', 'subject', 'subject_name',
            'grade_level', 'time_limit', 'is_active', 'allow_multiple_attempts',
            'created_by', 'created_by_name', 'question_count', 'created_at'
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.full_name

    def get_question_count(self, obj):
        return obj.questions.count()


class QuizDetailSerializer(serializers.ModelSerializer):
    """Full quiz detail with all questions and choices (no answers)."""
    questions = QuestionSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    grade_level = serializers.IntegerField(source='subject.grade_level', read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            'quiz_id', 'title', 'description', 'quiz_type', 'subject', 'subject_name',
            'grade_level', 'time_limit', 'is_active', 'allow_multiple_attempts',
            'show_answers_after_submit', 'created_by', 'created_by_name',
            'questions', 'created_at', 'updated_at'
        ]

    def get_created_by_name(self, obj):
        return obj.created_by.full_name


# ── Write Serializers (for creating quizzes) ─────────────────────────────────

class ChoiceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['text', 'is_correct', 'order']


class QuestionWriteSerializer(serializers.ModelSerializer):
    choices = ChoiceWriteSerializer(many=True)

    class Meta:
        model = Question
        fields = ['text', 'order', 'image', 'choices']


class QuizCreateSerializer(serializers.ModelSerializer):
    questions = QuestionWriteSerializer(many=True)

    class Meta:
        model = Quiz
        fields = [
            'title', 'description', 'subject', 'quiz_type',
            'time_limit', 'allow_multiple_attempts', 'show_answers_after_submit',
            'questions'
        ]

    def validate_subject(self, value):
        request = self.context.get('request')
        if request and request.user.role == 1:  # ROLE_TEACHER
            if value.teacher != request.user:
                raise serializers.ValidationError("You can only create quizzes for your own subjects.")
        return value

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        quiz = Quiz.objects.create(created_by=self.context['request'].user, **validated_data)

        for q_data in questions_data:
            choices_data = q_data.pop('choices')
            question = Question.objects.create(quiz=quiz, **q_data)
            for c_data in choices_data:
                Choice.objects.create(question=question, **c_data)

        return quiz
