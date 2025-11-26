from rest_framework import serializers
from .models import Meal, FoodItem
from django.utils import timezone


class MealSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')
    total_calories = serializers.ReadOnlyField()
    total_protein = serializers.ReadOnlyField()
    total_carbohydrates = serializers.ReadOnlyField()
    total_fats = serializers.ReadOnlyField()
    macros_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Meal
        fields = [
            'id', 'user', 'meal_type', 'name', 'description',
            'calories', 'protein', 'carbohydrates', 'fats',
            'fiber', 'sugar', 'sodium',
            'serving_size', 'servings',
            'total_calories', 'total_protein', 'total_carbohydrates', 'total_fats',
            'macros_percentage',
            'meal_date', 'meal_time', 'notes', 'photo_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_meal_date(self, value):
        """Ensure meal date is not in the future"""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Meal date cannot be in the future."
            )
        return value

    def validate_calories(self, value):
        """Ensure calories is positive"""
        if value < 0:
            raise serializers.ValidationError("Calories must be positive.")
        return value

    def validate_servings(self, value):
        """Ensure servings is positive"""
        if value <= 0:
            raise serializers.ValidationError("Servings must be greater than 0.")
        return value


class MealCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating meals with minimal required fields"""

    class Meta:
        model = Meal
        fields = [
            'meal_type', 'name', 'description',
            'calories', 'protein', 'carbohydrates', 'fats',
            'fiber', 'sugar', 'sodium',
            'serving_size', 'servings',
            'meal_date', 'meal_time', 'notes', 'photo_url'
        ]

    def validate_meal_date(self, value):
        """Ensure meal date is not in the future"""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Meal date cannot be in the future."
            )
        return value


class MealUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating meals"""

    class Meta:
        model = Meal
        fields = [
            'meal_type', 'name', 'description',
            'calories', 'protein', 'carbohydrates', 'fats',
            'fiber', 'sugar', 'sodium',
            'serving_size', 'servings',
            'meal_date', 'meal_time', 'notes', 'photo_url'
        ]


class NutritionSummarySerializer(serializers.Serializer):
    """Serializer for nutrition statistics and summaries"""
    total_meals = serializers.IntegerField()
    total_calories = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_protein = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_carbohydrates = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_fats = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_fiber = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_sugar = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_sodium = serializers.DecimalField(max_digits=10, decimal_places=2)
    avg_calories_per_meal = serializers.DecimalField(max_digits=10, decimal_places=2)
    meal_types_breakdown = serializers.DictField()
    macros_percentage = serializers.DictField()


class FoodItemSerializer(serializers.ModelSerializer):
    """Serializer for food items"""
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'description', 'category',
            'calories', 'protein', 'carbohydrates', 'fats',
            'fiber', 'sugar', 'sodium',
            'serving_size', 'serving_unit', 'is_active',
            'is_custom', 'created_by', 'created_by_email',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_custom', 'created_by', 'created_at', 'updated_at']


class FoodItemListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing food items"""

    class Meta:
        model = FoodItem
        fields = [
            'id', 'name', 'category', 'calories',
            'protein', 'carbohydrates', 'fats', 'serving_size'
        ]
