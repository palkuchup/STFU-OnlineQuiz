from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin-dashboard/users/', views.admin_users, name='admin-users'),
    path('admin-dashboard/subjects/', views.admin_subjects, name='admin-subjects'),
    path('admin-dashboard/registration-requests/', views.admin_registration_requests, name='admin-reg-requests'),
    # Teacher
    path('teacher/', views.teacher_dashboard, name='teacher-dashboard'),
    path('teacher/quizzes/', views.teacher_quizzes, name='teacher-quizzes'),
    path('teacher/quizzes/<uuid:quiz_id>/results/', views.teacher_quiz_results, name='teacher-quiz-results'),
    path('teacher/students/', views.teacher_students, name='teacher-students'),
    # Student
    path('student/', views.student_dashboard, name='student-dashboard'),
    path('student/quizzes/', views.student_quizzes, name='student-quizzes'),
    path('student/history/', views.student_history, name='student-history'),
]
