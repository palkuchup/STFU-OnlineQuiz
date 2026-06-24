from django.urls import path
from . import views

urlpatterns = [
    path('', views.SubjectListView.as_view(), name='api-subjects'),
    path('<uuid:subject_id>/', views.SubjectDetailView.as_view(), name='api-subject-detail'),
    path('enrollments/', views.EnrollmentListView.as_view(), name='api-enrollments'),
    path('final-grade/', views.SubmitFinalGradeView.as_view(), name='api-final-grade'),
]
