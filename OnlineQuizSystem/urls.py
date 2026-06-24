from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Web UI routes
    path('', include('dashboard.urls')),
    # REST API routes
    path('api/auth/', include('accounts.urls')),
    path('api/subjects/', include('subjects.urls')),
    path('api/quizzes/', include('quizzes.urls')),
    path('api/results/', include('results.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
