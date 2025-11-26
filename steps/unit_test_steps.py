import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from datetime import date, timedelta
from .models import StepGoal, DailySteps, StepStreak
from django.db.utils import IntegrityError
from rest_framework import serializers
from .serializers import StepGoalSerializer, DailyStepsSerializer


# --- Model Tests ---

@pytest.mark.django_db
class TestStepGoalModel:
    def test_create_step_goal(self, user):
        """Test creating a StepGoal instance."""
        goal = StepGoal.objects.create(user=user, daily_goal=8000)
        assert goal.user == user
        assert goal.daily_goal == 8000
        assert str(goal) == f"{user.username}'s goal: 8,000 steps/day"
        assert StepGoal.objects.count() == 1

    def test_default_daily_goal(self, user):
        """Test the default value for daily_goal."""
        goal = StepGoal.objects.create(user=user)
        assert goal.daily_goal == 10000

    def test_goal_validators(self, user):
        """Test MinValueValidator and MaxValueValidator constraints."""
        with pytest.raises(ValidationError):
            goal = StepGoal(user=user, daily_goal=500)
            goal.full_clean()

        with pytest.raises(ValidationError):
            goal = StepGoal(user=user, daily_goal=150000)
            goal.full_clean()

    def test_one_to_one_constraint(self, user):
        """Test that a user can only have one step goal."""
        StepGoal.objects.create(user=user, daily_goal=5000)
        with pytest.raises(IntegrityError):
            StepGoal.objects.create(user=user, daily_goal=7000)


@pytest.mark.django_db
class TestDailyStepsModel:
    def test_create_daily_steps(self, user):
        """Test creating a DailySteps instance with all fields."""
        steps_entry = DailySteps.objects.create(
            user=user,
            date=date.today(),
            steps=15000,
            distance_km=12.0,
            calories_burned=600,
            active_minutes=90,
            source='fitbit'
        )
        assert steps_entry.user == user
        assert steps_entry.steps == 15000
        assert steps_entry.distance_km == 12.0
        assert steps_entry.calories_burned == 600
        assert steps_entry.source == 'fitbit'
        assert str(steps_entry) == f"{user.username} - {date.today()}: 15,000 steps"
        assert DailySteps.objects.count() == 1

    def test_auto_calculation_on_save(self, user):
        """Test that distance and calories are auto-calculated if not provided."""
        steps_entry = DailySteps(user=user, date=date.today(), steps=12500)
        steps_entry.save()

        # 12500 steps / 1250 steps/km = 10.0 km
        assert float(steps_entry.distance_km) == 10.0
        # 12500 steps * 0.05 calories/step = 625 calories
        assert steps_entry.calories_burned == 625

    def test_auto_calculation_not_overwritten(self, user):
        """Test that provided values are not overwritten by auto-calculation."""
        steps_entry = DailySteps(user=user, date=date.today(), steps=1000, distance_km=0.5, calories_burned=50)
        steps_entry.save()

        assert float(steps_entry.distance_km) == 0.5
        assert steps_entry.calories_burned == 50

    def test_unique_together_constraint(self, user):
        """Test that a user cannot have multiple step entries for the same day."""
        date_today = date.today()
        DailySteps.objects.create(user=user, date=date_today, steps=10000)
        with pytest.raises(IntegrityError):
            DailySteps.objects.create(user=user, date=date_today, steps=5000)

    def test_goal_achieved_property(self, user):
        """Test the goal_achieved property."""
        StepGoal.objects.create(user=user, daily_goal=10000)
        entry_met = DailySteps.objects.create(user=user, date=date.today(), steps=11000)
        entry_not_met = DailySteps.objects.create(user=user, date=date.today() - timedelta(days=1), steps=9000)

        assert entry_met.goal_achieved is True
        assert entry_not_met.goal_achieved is False

    def test_goal_achieved_no_goal(self, user):
        """Test goal_achieved property when no goal is set."""
        entry = DailySteps.objects.create(user=user, date=date.today(), steps=10000)
        assert entry.goal_achieved is False

    def test_goal_percentage_property(self, user):
        """Test the goal_percentage property."""
        StepGoal.objects.create(user=user, daily_goal=10000)
        entry_110 = DailySteps.objects.create(user=user, date=date.today(), steps=11000)
        entry_90 = DailySteps.objects.create(user=user, date=date.today() - timedelta(days=1), steps=9000)

        assert entry_110.goal_percentage == 110.0
        assert entry_90.goal_percentage == 90.0

    def test_estimated_properties_fallbacks(self, user):
        """Test estimated_distance_km and estimated_calories fallbacks."""
        entry = DailySteps.objects.create(user=user, date=date.today(), steps=12500)
        # Values are automatically set by the `save` method, so properties should return those.
        assert entry.estimated_distance_km == 10.0
        assert entry.estimated_calories == 625

        entry_with_data = DailySteps.objects.create(user=user, date=date.today() - timedelta(days=1), steps=100,
                                                    distance_km=0.1, calories_burned=5)
        assert entry_with_data.estimated_distance_km == 0.1
        assert entry_with_data.estimated_calories == 5


@pytest.mark.django_db
class TestStepStreakModel:
    def test_create_step_streak(self, user):
        """Test creating a StepStreak instance."""
        streak = StepStreak.objects.create(user=user)
        assert streak.user == user
        assert streak.current_streak == 0
        assert streak.longest_streak == 0
        assert streak.last_updated == date.today()
        assert str(streak) == f"{user.username}'s streak: 0 days"

    def test_update_streak_met_goal(self, user):
        """Test update_streak when the goal was met yesterday."""
        StepGoal.objects.create(user=user, daily_goal=10000)
        yesterday = date.today() - timedelta(days=1)
        DailySteps.objects.create(user=user, date=yesterday, steps=12000)
        streak = StepStreak.objects.create(user=user, last_updated=yesterday)

        streak.update_streak()

        assert streak.current_streak == 1
        assert streak.longest_streak == 1
        assert streak.total_days_goal_met == 1
        assert streak.last_updated == date.today()

    def test_update_streak_not_met_goal(self, user):
        """Test update_streak when the goal was not met yesterday."""
        StepGoal.objects.create(user=user, daily_goal=10000)
        yesterday = date.today() - timedelta(days=1)
        DailySteps.objects.create(user=user, date=yesterday, steps=8000)
        streak = StepStreak.objects.create(user=user, last_updated=yesterday, current_streak=5, longest_streak=5)

        streak.update_streak()

        assert streak.current_streak == 0
        assert streak.longest_streak == 5  # Longest streak remains
        assert streak.last_updated == date.today()


    def test_update_streak_already_updated_today(self, user):
        """Test update_streak does nothing if already updated today."""
        StepGoal.objects.create(user=user, daily_goal=10000)
        yesterday = date.today() - timedelta(days=1)
        DailySteps.objects.create(user=user, date=yesterday, steps=12000)
        streak = StepStreak.objects.create(user=user, last_updated=date.today(), current_streak=1)

        streak.update_streak()

        assert streak.current_streak == 1  # Should not change
        assert streak.last_updated == date.today()


# --- Serializer Tests (using DRF test client implicitly via pytest-django db marker) ---

@pytest.mark.django_db
class TestStepGoalSerializer:
    def test_serializer_validation(self):
        """Test custom validation logic in the serializer."""
        serializer = StepGoalSerializer(data={'daily_goal': 500})
        assert not serializer.is_valid()
        assert 'daily_goal' in serializer.errors

        serializer = StepGoalSerializer(data={'daily_goal': 150000})
        assert not serializer.is_valid()
        assert 'daily_goal' in serializer.errors

        serializer = StepGoalSerializer(data={'daily_goal': 5000})
        assert serializer.is_valid()


@pytest.mark.django_db
class TestDailyStepsSerializer:

    def test_serializer_read_only_fields(self, user):
        """Test that read-only fields are included in output but ignored on input."""
        StepGoal.objects.create(user=user, daily_goal=10000)
        data = {
            'user': user.id,
            'date': date.today().isoformat(),
            'steps': 12000,
            'source': 'manual'
        }
        serializer = DailyStepsSerializer(data=data)
        assert serializer.is_valid()
        daily_steps_instance = serializer.save(user=user)

        # Check output representation includes read-only computed properties
        output_data = DailyStepsSerializer(daily_steps_instance).data
        assert output_data['goal_achieved'] is True
        assert output_data['goal_percentage'] == 120.0
        assert output_data['user_email'] == user.email
