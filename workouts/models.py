from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Workout(models.Model):
    WORKOUT_TYPES = [
        ('running', 'Running'),
        ('cycling', 'Cycling'),
        ('swimming', 'Swimming'),
        ('walking', 'Walking'),
        ('gym', 'Gym Workout'),
        ('yoga', 'Yoga'),
        ('pilates', 'Pilates'),
        ('hiit', 'HIIT'),
        ('cardio', 'Cardio'),
        ('strength', 'Strength Training'),
        ('sports', 'Sports'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='workouts'
    )
    workout_type = models.CharField(
        max_length=20,
        choices=WORKOUT_TYPES,
        default='other'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(
        help_text="Duration in minutes",
        null=True,
        blank=True
    )
    calories_burned = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Calories burned"
    )
    distance = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Distance in kilometers"
    )
    intensity = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )
    notes = models.TextField(blank=True, null=True)
    workout_date = models.DateField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'workouts'
        ordering = ['-workout_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'workout_date']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.title} - {self.workout_date}"

    @property
    def duration_display(self):
        """Return formatted duration"""
        if self.duration:
            hours = self.duration // 60
            minutes = self.duration % 60
            if hours > 0:
                return f"{hours}h {minutes}m"
            return f"{minutes}m"
        return "N/A"

class Goal(models.Model):
    """Model for tracking fitness goals"""
    GOAL_TYPES = [
        ('running', 'Running (km)'),
        ('cycling', 'Cycling (km)'),
        ('swimming', 'Swimming (km)'),
        ('walking', 'Walking (km)'),
        ('weight', 'Weight (kg)'),
        ('calories', 'Calories Burned'),
        ('workouts', 'Number of Workouts'),
        ('strength', 'Strength Training (sessions)'),
        ('yoga', 'Yoga (sessions)'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='goals'
    )
    goal_type = models.CharField(
        max_length=20,
        choices=GOAL_TYPES,
        default='other'
    )
    title = models.CharField(max_length=200, blank=True)
    target_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Target value to achieve"
    )
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Current progress toward the goal"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-end_date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_completed']),
            models.Index(fields=['user', 'goal_type']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        return f"{self.get_goal_type_display()}: {self.current_value}/{self.target_value} ({self.user.username})"

    def save(self, *args, **kwargs):
        # Auto-generate title if not provided
        if not self.title:
            self.title = f"{self.get_goal_type_display()} Goal"
        
        # Check if goal is completed
        if not self.is_completed and self.current_value >= self.target_value:
            self.is_completed = True
            self.completed_at = timezone.now()
        
        # If current value is updated to be less than target, mark as not completed
        elif self.is_completed and self.current_value < self.target_value:
            self.is_completed = False
            self.completed_at = None
        
        super().save(*args, **kwargs)

    @property
    def progress_percentage(self):
        """Return completion percentage (0-100)"""
        if self.target_value == 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)

    @property
    def time_remaining(self):
        """Return number of days remaining until end date"""
        today = timezone.now().date()
        if self.end_date < today:
            return 0
        return (self.end_date - today).days

    @property
    def is_active(self):
        """Check if the goal is currently active"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and not self.is_completed

    @property
    def unit(self):
        """Get the appropriate unit for the goal type"""
        unit_map = {
            'running': 'km',
            'cycling': 'km',
            'swimming': 'km',
            'walking': 'km',
            'weight': 'kg',
            'calories': 'cal',
            'workouts': 'workouts',
            'strength': 'sessions',
            'yoga': 'sessions',
            'other': ''
        }
        return unit_map.get(self.goal_type, '')

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate end date is after start date
        if self.end_date <= self.start_date:
            raise ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        # Validate target value is positive
        if self.target_value <= 0:
            raise ValidationError({
                'target_value': 'Target value must be greater than zero'
            })
        
        # Validate current value is not negative
        if self.current_value < 0:
            raise ValidationError({
                'current_value': 'Current value cannot be negative'
            })
