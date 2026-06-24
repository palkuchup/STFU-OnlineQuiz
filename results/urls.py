from django.urls import path
from . import views

urlpatterns = [
    # Student
    path('quizzes/<uuid:quiz_id>/start/', views.StartAttemptView.as_view(), name='api-start-attempt'),
    path('attempts/<uuid:attempt_id>/submit/', views.SubmitAttemptView.as_view(), name='api-submit-attempt'),
    path('attempts/<uuid:attempt_id>/', views.AttemptDetailView.as_view(), name='api-attempt-detail'),
    path('history/', views.StudentHistoryView.as_view(), name='api-student-history'),
    # Teacher
    path('quiz/<uuid:quiz_id>/results/', views.TeacherResultsView.as_view(), name='api-quiz-results'),
    path('subject/<uuid:subject_id>/results/', views.TeacherSubjectResultsView.as_view(), name='api-subject-results'),
]
