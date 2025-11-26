import pytest
from authentication.models import User
from django.utils import timezone
from datetime import date, timedelta
from workouts.models import Workout
from django.conf import settings
from django.db import models


# Use the Django database for tests
pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    """Fixture to create a sample user"""
    return User.objects.create_user(username='testuser', email='test@example.com', password='testpassword123')


@pytest.fixture
def sample_workout(user):
    """Fixture to create a sample Workout instance"""
    return Workout.objects.create(
        user=user,
        title="Morning Run",
        workout_type="running",
        duration=45,
        distance=5.2,
        intensity="medium",
        status="completed",
        workout_date=date.today(),
    )


def test_workout_creation(user):
    """Test that a Workout instance can be created correctly"""
    workout = Workout.objects.create(
        user=user,
        title="Evening Walk",
        workout_type="walking",
        duration=30,
        workout_date=date.today(),
    )
    assert workout.id is not None
    assert workout.user == user
    assert workout.title == "Evening Walk"
    assert workout.get_workout_type_display() == "Walking"
    assert workout.status == "planned"  # Default value
    assert workout.duration == 30


def test_workout_str_representation(sample_workout):
    """Test the __str__ method of the Workout model"""
    expected_str = f"Morning Run - {date.today()}"
    assert str(sample_workout) == expected_str


def test_duration_display_property(sample_workout):
    """Test the duration_display property for various durations"""
    # Test minutes
    assert sample_workout.duration_display == "45m"

    # Test hours and minutes
    sample_workout.duration = 125
    assert sample_workout.duration_display == "2h 5m"

    # Test N/A for null duration
    sample_workout.duration = None
    assert sample_workout.duration_display == "N/A"


def test_workout_defaults(user):
    """Test that default values are applied correctly"""
    today = date.today()
    workout = Workout.objects.create(
        user=user,
        title="Default Test",
        workout_date=today
    )
    assert workout.workout_type == "other"
    assert workout.intensity == "medium"
    assert workout.status == "planned"
    assert workout.created_at is not None
    assert workout.updated_at is not None


def test_meta_options():
    """Test database table name and ordering"""
    assert Workout._meta.db_table == 'workouts'
    # Test ordering: ['-workout_date', '-created_at']
    assert Workout._meta.ordering == ['-workout_date', '-created_at']


def test_indexes_exist():
    """Test that the specified database indexes are created"""
    # Get all indexes from the model's _meta
    indexes = Workout._meta.indexes
    
    # Check that we have the expected number of indexes (2)
    assert len(indexes) == 2, f"Expected 2 indexes, found {len(indexes)}"
    
    # Check that the indexes exist with the correct fields
    has_user_workout_date = any(
        set(index.fields) == {'user', 'workout_date'} 
        for index in indexes
    )
    has_user_status = any(
        set(index.fields) == {'user', 'status'}
        for index in indexes
    )
    
    assert has_user_workout_date, "Index on (user, workout_date) not found"
    assert has_user_status, "Index on (user, status) not found"


def test_field_help_texts():
    """Test the help_text for specific fields"""
    # Access fields via _meta API for comprehensive checks
    duration_help_text = Workout._meta.get_field('duration').help_text
    calories_help_text = Workout._meta.get_field('calories_burned').help_text
    distance_help_text = Workout._meta.get_field('distance').help_text

    assert duration_help_text == "Duration in minutes"
    assert calories_help_text == "Calories burned"
    assert distance_help_text == "Distance in kilometers"
