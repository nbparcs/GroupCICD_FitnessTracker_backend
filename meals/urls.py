from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MealViewSet, FoodItemViewSet

router = DefaultRouter()
router.register(r'meals', MealViewSet, basename='meal')
router.register(r'food-items', FoodItemViewSet, basename='food-item')

urlpatterns = [
    path('', include(router.urls)),
]
