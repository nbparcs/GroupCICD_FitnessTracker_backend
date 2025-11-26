from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


# Use Django's built-in UserAdmin to get password hashing and permissions UI
admin.site.register(User, BaseUserAdmin)
