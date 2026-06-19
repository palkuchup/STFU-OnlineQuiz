from django.contrib import admin
from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'email', 'role')
    search_fields = ['username', 'email']
    list_per_page = 20


admin.site.register(CustomUser, CustomUserAdmin)
