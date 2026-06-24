from django.urls import path
from . import views

urlpatterns = [
    path('', views.QuizListView.as_view(), name='api-quizzes'),
    path('create/', views.QuizCreateView.as_view(), name='api-quiz-create'),
    path('<uuid:quiz_id>/', views.QuizDetailView.as_view(), name='api-quiz-detail'),
    path('<uuid:quiz_id>/toggle-active/', views.QuizToggleActiveView.as_view(), name='api-quiz-toggle'),
    path('<uuid:quiz_id>/edit/', views.QuizUpdateView.as_view(), name='api-quiz-edit'),
    path('<uuid:quiz_id>/delete/', views.QuizDeleteView.as_view(), name='api-quiz-delete'),
]
