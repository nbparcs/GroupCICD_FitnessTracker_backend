from rest_framework import serializers
from .models import Workout, Goal
from django.utils import timezone


class WorkoutSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')
    duration_display = serializers.ReadOnlyField()

    class Meta:
        model = Workout
        fields = [
            'id', 'user', 'workout_type', 'title', 'description',
            'duration', 'duration_display', 'calories_burned', 'distance',
            'intensity', 'status', 'notes', 'workout_date',
            'started_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_workout_date(self, value):
        """Ensure workout date is not in the future"""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Workout date cannot be in the future."
            )
        return value

    def validate(self, data):
        """Custom validation for workout data"""
        # If status is completed, ensure we have duration
        if data.get('status') == 'completed' and not data.get('duration'):
            raise serializers.ValidationError({
                'duration': 'Duration is required for completed workouts.'
            })

        # If distance is provided, ensure it's positive
        if data.get('distance') and data.get('distance') <= 0:
            raise serializers.ValidationError({
                'distance': 'Distance must be greater than 0.'
            })

        # If calories_burned is provided, ensure it's positive
        if data.get('calories_burned') and data.get('calories_burned') <= 0:
            raise serializers.ValidationError({
                'calories_burned': 'Calories burned must be greater than 0.'
            })

        return data


class GoalSerializer(serializers.ModelSerializer):
    """Serializer for the Goal model"""
    user = serializers.ReadOnlyField(source='user.email')
    progress_percentage = serializers.ReadOnlyField()
    time_remaining = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    unit = serializers.ReadOnlyField()

    class Meta:
        model = Goal
        fields = [
            'id', 'user', 'goal_type', 'title', 'target_value', 
            'current_value', 'progress_percentage', 'start_date', 
            'end_date', 'time_remaining', 'is_active', 'is_completed',
            'completed_at', 'notes', 'created_at', 'updated_at', 'unit'
        ]
        read_only_fields = [
            'id', 'user', 'is_completed', 'completed_at',
            'created_at', 'updated_at', 'progress_percentage',
            'time_remaining', 'is_active', 'unit'
        ]

    def validate(self, data):
        """Custom validation for goal data"""
        # Ensure end date is after start date
        start_date = data.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = data.get('end_date', getattr(self.instance, 'end_date', None))
        
        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })

        # Ensure target value is positive
        target_value = data.get('target_value', getattr(self.instance, 'target_value', None))
        if target_value is not None and target_value <= 0:
            raise serializers.ValidationError({
                'target_value': 'Target value must be greater than zero.'
            })

        # Ensure current value is not negative
        current_value = data.get('current_value', getattr(self.instance, 'current_value', 0))
        if current_value < 0:
            raise serializers.ValidationError({
                'current_value': 'Current value cannot be negative.'
            })

        return data

    def create(self, validated_data):
        """Set the current user as the goal owner"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class WorkoutCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating workouts with minimal required fields"""

    class Meta:
        model = Workout
        fields = [
            'workout_type', 'title', 'description', 'duration',
            'calories_burned', 'distance', 'intensity', 'status',
            'notes', 'workout_date'
        ]

    def validate_workout_date(self, value):
        """Ensure workout date is not in the future"""
        if value > timezone.now().date():
            raise serializers.ValidationError(
                "Workout date cannot be in the future."
            )
        return value


class WorkoutUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating workouts"""

    class Meta:
        model = Workout
        fields = [
            'workout_type', 'title', 'description', 'duration',
            'calories_burned', 'distance', 'intensity', 'status',
            'notes', 'workout_date', 'started_at', 'completed_at'
        ]

    def validate(self, data):
        """Validate status transitions"""
        instance = self.instance
        new_status = data.get('status')
        
        if new_status and instance:
            current_status = instance.status
            
            # Prevent invalid status transitions
            if current_status == 'planned' and new_status == 'completed':
                raise serializers.ValidationError({
                    'status': 'Cannot mark a planned workout as completed. Please start the workout first.'
                })
                
            # If marking as completed, ensure it was started
            if new_status == 'completed' and not instance.started_at:
                raise serializers.ValidationError({
                    'status': 'Cannot complete a workout that has not been started.'
                })
                
        return data

    def update(self, instance, validated_data):
        """Handle status changes and timestamps"""
        new_status = validated_data.get('status', instance.status)

        # Auto-set timestamps based on status
        if new_status == 'in_progress' and not instance.started_at:
            validated_data['started_at'] = timezone.now()

        if new_status == 'completed' and not instance.completed_at:
            validated_data['completed_at'] = timezone.now()

        return super().update(instance, validated_data)


class WorkoutSummarySerializer(serializers.Serializer):
    """Serializer for workout statistics and summaries"""
    total_workouts = serializers.IntegerField()
    total_duration = serializers.IntegerField()
    total_calories = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_distance = serializers.DecimalField(max_digits=10, decimal_places=2)
    completed_workouts = serializers.IntegerField()
    workout_types = serializers.DictField()
