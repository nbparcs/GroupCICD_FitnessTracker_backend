from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, timedelta

User = settings.AUTH_USER_MODEL


class StepGoal(models.Model):
    """User's daily step goal"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='step_goal')
    daily_goal = models.IntegerField(
        default=10000,
        validators=[MinValueValidator(1000), MaxValueValidator(100000)],
        help_text="Daily step goal (1,000 - 100,000)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'step_goals'
        verbose_name = 'Step Goal'
        verbose_name_plural = 'Step Goals'

    def __str__(self):
        return f"{self.user.username}'s goal: {self.daily_goal:,} steps/day"


class DailySteps(models.Model):
    """Daily step count records"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_steps')
    date = models.DateField(default=date.today, db_index=True)
    steps = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(200000)],
        help_text="Number of steps taken (0 - 200,000)"
    )
    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Distance covered in kilometers"
    )
    calories_burned = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Estimated calories burned"
    )
    active_minutes = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        help_text="Active minutes (0 - 1440)"
    )
    notes = models.TextField(blank=True, null=True)
    source = models.CharField(
        max_length=50,
        default='manual',
        choices=[
            ('manual', 'Manual Entry'),
            ('fitbit', 'Fitbit'),
            ('apple_health', 'Apple Health'),
            ('google_fit', 'Google Fit'),
            ('samsung_health', 'Samsung Health'),
            ('other', 'Other'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_steps'
        verbose_name = 'Daily Steps'
        verbose_name_plural = 'Daily Steps'
        unique_together = ['user', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', '-date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date}: {self.steps:,} steps"

    @property
    def goal_achieved(self):
        """Check if daily goal was achieved"""
        try:
            goal = self.user.step_goal.daily_goal
            return self.steps >= goal
        except StepGoal.DoesNotExist:
            return False

    @property
    def goal_percentage(self):
        """Calculate percentage of goal achieved"""
        try:
            goal = self.user.step_goal.daily_goal
            if goal > 0:
                return round((self.steps / goal) * 100, 1)
            return 0
        except StepGoal.DoesNotExist:
            return 0

    @property
    def estimated_distance_km(self):
        """Estimate distance if not provided (average stride length)"""
        if self.distance_km:
            return float(self.distance_km)
        # Average: 1 km = 1,250 steps
        return round(self.steps / 1250, 2)

    @property
    def estimated_calories(self):
        """Estimate calories if not provided"""
        if self.calories_burned:
            return self.calories_burned
        # Average: 100 steps = 5 calories
        return round(self.steps * 0.05)

    def save(self, *args, **kwargs):
        # Auto-calculate distance if not provided
        if not self.distance_km and self.steps > 0:
            self.distance_km = round(self.steps / 1250, 2)

        # Auto-calculate calories if not provided
        if not self.calories_burned and self.steps > 0:
            self.calories_burned = round(self.steps * 0.05)

        super().save(*args, **kwargs)


class StepStreak(models.Model):
    """Track user's step goal streaks"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='step_streak')
    current_streak = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    longest_streak = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_updated = models.DateField(default=date.today)
    total_days_goal_met = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'step_streaks'
        verbose_name = 'Step Streak'
        verbose_name_plural = 'Step Streaks'

    def __str__(self):
        return f"{self.user.username}'s streak: {self.current_streak} days"

    def update_streak(self):
        """Update streak based on recent step records"""
        try:
            goal = self.user.step_goal.daily_goal
        except StepGoal.DoesNotExist:
            return

        today = date.today()

        # Check if already updated today
        if self.last_updated == today:
            return

        # Get yesterday's steps
        yesterday = today - timedelta(days=1)
        try:
            yesterday_steps = DailySteps.objects.get(user=self.user, date=yesterday)
            if yesterday_steps.steps >= goal:
                self.current_streak += 1
                self.total_days_goal_met += 1
                if self.current_streak > self.longest_streak:
                    self.longest_streak = self.current_streak
            else:
                self.current_streak = 0
        except DailySteps.DoesNotExist:
            # If no record for yesterday, check if it's more than 1 day gap
            if self.last_updated < yesterday:
                self.current_streak = 0

        self.last_updated = today
        self.save()


from django.db import models

# Create your models here.
