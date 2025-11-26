from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkoutViewSet, GoalViewSet

router = DefaultRouter()
router.register(r'workouts', WorkoutViewSet, basename='workout')
router.register(r'goals', GoalViewSet, basename='goal')

urlpatterns = [
    path('', include(router.urls)),
]
