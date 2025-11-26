from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserLoginView,
    UserLogoutView,
    UserProfileView
)

urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
]
