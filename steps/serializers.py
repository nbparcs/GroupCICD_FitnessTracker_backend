from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DailySteps, StepGoal, StepStreak
from datetime import date, timedelta


class StepGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StepGoal
        fields = ['id', 'daily_goal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_daily_goal(self, value):
        if value < 1000:
            raise serializers.ValidationError("Daily goal must be at least 1,000 steps")
        if value > 100000:
            raise serializers.ValidationError("Daily goal cannot exceed 100,000 steps")
        return value


class DailyStepsSerializer(serializers.ModelSerializer):
    goal_achieved = serializers.BooleanField(read_only=True)
    goal_percentage = serializers.FloatField(read_only=True)
    estimated_distance_km = serializers.FloatField(read_only=True)
    estimated_calories = serializers.IntegerField(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = DailySteps
        fields = [
            'id', 'user', 'user_email', 'date', 'steps', 'distance_km',
            'calories_burned', 'active_minutes', 'notes', 'source',
            'goal_achieved', 'goal_percentage', 'estimated_distance_km',
            'estimated_calories', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_date(self, value):
        if value > date.today():
            raise serializers.ValidationError("Cannot log steps for future dates")
        return value

    def validate_steps(self, value):
        if value < 0:
            raise serializers.ValidationError("Steps cannot be negative")
        if value > 200000:
            raise serializers.ValidationError("Steps seem unrealistic (max: 200,000)")
        return value

    def validate(self, data):
        # Check for duplicate date entry
        request = self.context.get('request')
        if request and request.user:
            date_value = data.get('date', date.today())
            existing = DailySteps.objects.filter(
            user=request.user,
            date=date_value
            ).exclude(pk=self.instance.pk if self.instance else None)
            if existing.exists():
                raise serializers.ValidationError(
                    {"date": "You already have a step record for this date"}
                )

        return data

    class StepStreakSerializer(serializers.ModelSerializer):
        user_email = serializers.EmailField(source='user.email', read_only=True)

        class Meta:
            model = StepStreak
            fields = [
                'id', 'user', 'user_email', 'current_streak', 'longest_streak',
                'last_updated', 'total_days_goal_met', 'created_at', 'updated_at'
            ]
            read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class StepSummarySerializer(serializers.Serializer):
    """Serializer for step statistics and summaries"""
    total_steps = serializers.IntegerField()
    total_distance_km = serializers.FloatField()
    total_calories = serializers.IntegerField()
    total_active_minutes = serializers.IntegerField()
    average_steps = serializers.FloatField()
    average_distance_km = serializers.FloatField()
    average_calories = serializers.FloatField()
    days_recorded = serializers.IntegerField()
    days_goal_met = serializers.IntegerField()
    goal_achievement_rate = serializers.FloatField()
    highest_steps = serializers.IntegerField()
    highest_steps_date = serializers.DateField()
    current_streak = serializers.IntegerField()
    longest_streak = serializers.IntegerField()

class WeeklyStepsSerializer(serializers.Serializer):
    """Serializer for weekly step data"""
    date = serializers.DateField()
    steps = serializers.IntegerField()
    goal_achieved = serializers.BooleanField()
    day_name = serializers.CharField()


class StepStreakSerializer:
    pass