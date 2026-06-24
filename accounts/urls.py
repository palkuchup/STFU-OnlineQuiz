from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='api-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='api-token-refresh'),
    # Student self-registration
    path('register/', views.StudentRegisterView.as_view(), name='api-register'),
    # Profile
    path('me/', views.MeView.as_view(), name='api-me'),
    # Admin — user management
    path('users/', views.UserListView.as_view(), name='api-users'),
    # Admin — registration requests
    path('registration-requests/', views.RegistrationRequestListView.as_view(), name='api-reg-requests'),
    path('registration-requests/<uuid:request_id>/', views.RegistrationRequestDetailView.as_view(), name='api-reg-request-detail'),
]
