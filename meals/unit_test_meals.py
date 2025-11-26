import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from datetime import date
from meals.models import Meal
from meals.serializers import MealSerializer

# Get the custom User model
User = get_user_model()

# Use Django's database for tests. The @pytest.mark.django_db decorator handles test database setup/teardown.


@pytest.mark.django_db
class TestMealModel:
    """Tests for the Meal Django model."""

    @pytest.fixture
    def user(self):
        """A pytest fixture to create a user instance for use in tests."""
        return User.objects.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

    @pytest.fixture
    def sample_meal_data(self, user):
        """A pytest fixture for common meal data."""
        return {
            'user': user,
            'name': 'Sample Breakfast',
            'meal_type': 'breakfast',
            'calories': Decimal('350.00'),
            'protein': Decimal('20.00'),
            'carbohydrates': Decimal('40.00'),
            'fats': Decimal('12.00'),
            'servings': Decimal('1.5'),
            'meal_date': date.today(),
        }

    def test_meal_creation(self, sample_meal_data):
        """Test that a Meal object can be successfully created."""
        meal = Meal.objects.create(**sample_meal_data)
        assert meal.id is not None
        assert meal.name == 'Sample Breakfast'
        assert meal.user.email == 'test@example.com'
        assert meal.meal_date == date.today()

    def test_str_representation(self, sample_meal_data):
        """Test the __str__ method of the Meal model."""
        meal = Meal.objects.create(**sample_meal_data)
        expected_str = f"Sample Breakfast - breakfast ({date.today()})"
        assert str(meal) == expected_str

    def test_total_calories_property(self, sample_meal_data):
        """Test the total_calories property calculates correctly."""
        meal = Meal.objects.create(**sample_meal_data)
        expected_total = 350.00 * 1.5
        assert meal.total_calories == expected_total

    def test_total_macros_properties(self, sample_meal_data):
        """Test total protein, carbohydrates, and fats properties."""
        meal = Meal.objects.create(**sample_meal_data)

        assert meal.total_protein == 20.00 * 1.5
        assert meal.total_carbohydrates == 40.00 * 1.5
        assert meal.total_fats == 12.00 * 1.5

    def test_macros_percentage_property(self, sample_meal_data):
        """Test the macros_percentage property calculates correctly."""
        # 1g protein=4 cal, 1g carbs=4 cal, 1g fat=9 cal
        # Per serving: Prot=20g, Carbs=40g, Fats=12g, Cals=350
        meal = Meal.objects.create(**sample_meal_data)
        total_cals = meal.total_calories  # 525.0
        protein_cals = (20 * 1.5) * 4  # 120.0
        carbs_cals = (40 * 1.5) * 4  # 240.0
        fats_cals = (12 * 1.5) * 9  # 162.0

        percentages = meal.macros_percentage
        assert percentages['protein'] == round((protein_cals / total_cals) * 100, 1)
        assert percentages['carbs'] == round((carbs_cals / total_cals) * 100, 1)
        assert percentages['fats'] == round((fats_cals / total_cals) * 100, 1)

    def test_zero_calorie_macros_percentage(self, user):
        """Test macros_percentage when total calories are zero."""
        meal = Meal.objects.create(
            user=user,
            name='Water',
            calories=Decimal('0.00'),
            protein=Decimal('0.00'),
            meal_date=date.today(),
        )
        assert meal.macros_percentage == {'protein': 0, 'carbs': 0, 'fats': 0}

    def test_validators_for_negative_values(self, user):
        """Test that negative values for nutritional info raise a ValidationError."""
        with pytest.raises(ValidationError):
            meal = Meal(
                user=user,
                name='Invalid Meal',
                calories=Decimal('-100.00'),
                meal_date=date.today()
            )
            # Full clean is required to trigger model field validators
            meal.full_clean()

    def test_servings_validator(self, user):
        """Test that servings below minimum (0.01) raise a ValidationError."""
        with pytest.raises(ValidationError):
            meal = Meal(
                user=user,
                name='Zero Servings',
                calories=Decimal('100.00'),
                servings=Decimal('0.00'),
                meal_date=date.today()
            )
            meal.full_clean()


@pytest.mark.django_db
class TestMealSerializer:
    """Tests for the Meal Django REST Framework serializer."""

    @pytest.fixture
    def user(self):
        """A pytest fixture to create a user instance for use in tests."""
        return User.objects.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

    @pytest.fixture
    def meal_instance(self, user):
        """A pytest fixture to create a Meal instance for serialization testing."""
        return Meal.objects.create(
            user=user,
            name='Test Meal Instance',
            meal_type='lunch',
            calories=Decimal('500.00'),
            protein=Decimal('30.00'),
            fats=Decimal('20.00'),
            carbohydrates=Decimal('50.00'),
            servings=Decimal('2.0'),
            meal_date=date.today(),
        )

    def test_serializer_contains_expected_fields(self, meal_instance):
        """Test that the serializer includes all expected fields."""
        serializer = MealSerializer(instance=meal_instance)
        data = serializer.data
        expected_fields = [
            'id', 'user', 'meal_type', 'name', 'description',
            'calories', 'protein', 'carbohydrates', 'fats',
            'fiber', 'sugar', 'sodium',
            'serving_size', 'servings',
            'total_calories', 'total_protein', 'total_carbohydrates', 'total_fats',
            'macros_percentage', 'meal_date', 'meal_time', 'notes', 'photo_url',
            'created_at', 'updated_at'  # Added these fields that are automatically included by the model
        ]
        assert set(data.keys()) == set(expected_fields)

    def test_serializer_read_only_fields(self, meal_instance):
        """Test that read-only fields (like calculated properties) are present and correct."""
        serializer = MealSerializer(instance=meal_instance)
        data = serializer.data

        assert data['user'] == meal_instance.user.email
        assert data['total_calories'] == meal_instance.total_calories
        assert data['macros_percentage']['protein'] == meal_instance.macros_percentage['protein']

    def test_serializer_invalid_data(self):
        """Test that the serializer handles invalid input gracefully."""
        invalid_data = {
            'name': 'Invalid Meal',
            'calories': '-100.00',  # Invalid value
            'meal_date': 'not a date',  # Invalid format
        }
        serializer = MealSerializer(data=invalid_data)
        assert not serializer.is_valid()
        assert 'calories' in serializer.errors
        assert 'meal_date' in serializer.errors
        # Note: 'user' is not in errors because it's a read-only field in the serializer
        # and is not required for validation


if __name__ == '__main__':
    # You would typically run these tests using the pytest command in your Django environment
    # e.g., `pytest apps/meals/tests/unit_test_meals.py` (adjust path as needed)
    pass
