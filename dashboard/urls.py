from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin-dashboard/users/', views.admin_users, name='admin-users'),
    path('admin-dashboard/users/<uuid:user_id>/edit/', views.admin_edit_user, name='admin-edit-user'),
    path('admin-dashboard/users/<uuid:user_id>/delete/', views.admin_delete_user, name='admin-delete-user'),
    path('admin-dashboard/subjects/', views.admin_subjects, name='admin-subjects'),
    path('admin-dashboard/subjects/<uuid:subject_id>/', views.admin_subject_detail, name='admin-subject-detail'),
    path('admin-dashboard/registration-requests/', views.admin_registration_requests, name='admin-reg-requests'),
    path('admin-dashboard/registration-requests/<uuid:request_id>/review/', views.admin_review_request, name='admin-review-request'),
    path('teacher/', views.teacher_dashboard, name='teacher-dashboard'),
    path('teacher/quizzes/', views.teacher_quizzes, name='teacher-quizzes'),
    path('teacher/quizzes/create/', views.teacher_create_quiz, name='teacher-create-quiz'),
    path('teacher/quizzes/subject/<uuid:subject_id>/', views.teacher_subject_quizzes, name='teacher-subject-quizzes'),
    path('teacher/quizzes/<uuid:quiz_id>/edit/', views.teacher_edit_quiz, name='teacher-edit-quiz'),
    path('teacher/quizzes/<uuid:quiz_id>/results/', views.teacher_quiz_results, name='teacher-quiz-results'),
    path('teacher/students/', views.teacher_students, name='teacher-students'),
    # Student
    path('student/', views.student_dashboard, name='student-dashboard'),
    path('student/quizzes/', views.student_quizzes, name='student-quizzes'),
    path('student/quizzes/subject/<uuid:subject_id>/', views.student_subject_quizzes, name='student-subject-quizzes'),
    path('student/quizzes/<uuid:quiz_id>/take/', views.student_take_quiz, name='student-take-quiz'),
    path('student/quizzes/<uuid:quiz_id>/submit/', views.student_submit_quiz, name='student-submit-quiz'),
    path('student/results/<uuid:attempt_id>/', views.student_quiz_result, name='student-quiz-result'),
    path('student/history/', views.student_history, name='student-history'),
]
