from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DailyStepsViewSet, StepGoalViewSet, StepStreakViewSet

router = DefaultRouter()
router.register(r'daily', DailyStepsViewSet, basename='daily-steps')
router.register(r'goals', StepGoalViewSet, basename='step-goals')
router.register(r'streaks', StepStreakViewSet, basename='step-streaks')

urlpatterns = [
    path('', include(router.urls)),
]
