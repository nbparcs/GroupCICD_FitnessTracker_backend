from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from django.utils import timezone


class Meal(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meals'
    )
    meal_type = models.CharField(
        max_length=20,
        choices=MEAL_TYPES,
        default='other'
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    # Nutritional Information
    calories = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Calories (kcal)"
    )
    protein = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Protein in grams"
    )
    carbohydrates = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Carbohydrates in grams"
    )
    fats = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Fats in grams"
    )
    fiber = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Fiber in grams"
    )
    sugar = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Sugar in grams"
    )
    sodium = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text="Sodium in milligrams"
    )

    # Serving Information
    serving_size = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="e.g., 1 cup, 100g, 1 piece"
    )
    servings = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.0,
        validators=[MinValueValidator(0.01)],
        help_text="Number of servings"
    )

    # Additional Information
    meal_date = models.DateField()
    meal_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    photo_url = models.URLField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'meals'
        ordering = ['-meal_date', '-meal_time', '-created_at']
        indexes = [
            models.Index(fields=['user', 'meal_date']),
            models.Index(fields=['user', 'meal_type']),
            models.Index(fields=['meal_date']),
        ]

    def __str__(self):
        return f"{self.name} - {self.meal_type} ({self.meal_date})"

    @property
    def total_calories(self):
        """Calculate total calories including servings"""
        return float(self.calories) * float(self.servings)

    @property
    def total_protein(self):
        """Calculate total protein including servings"""
        if self.protein:
            return float(self.protein) * float(self.servings)
        return 0

    @property
    def total_carbohydrates(self):
        """Calculate total carbohydrates including servings"""
        if self.carbohydrates:
            return float(self.carbohydrates) * float(self.servings)
        return 0

    @property
    def total_fats(self):
        """Calculate total fats including servings"""
        if self.fats:
            return float(self.fats) * float(self.servings)
        return 0

    @property
    def macros_percentage(self):
        """Calculate percentage of calories from each macro"""
        total_cal = self.total_calories
        if total_cal == 0:
            return {'protein': 0, 'carbs': 0, 'fats': 0}

        # 1g protein = 4 cal, 1g carbs = 4 cal, 1g fat = 9 cal
        protein_cal = self.total_protein * 4
        carbs_cal = self.total_carbohydrates * 4
        fats_cal = self.total_fats * 9

        return {
            'protein': round((protein_cal / total_cal) * 100, 1) if protein_cal else 0,
            'carbs': round((carbs_cal / total_cal) * 100, 1) if carbs_cal else 0,
            'fats': round((fats_cal / total_cal) * 100, 1) if fats_cal else 0,
        }


class FoodItem(models.Model):
    """Pre-defined food items for quick meal logging"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    # Nutritional Information (per serving)
    calories = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    protein = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    carbohydrates = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    fats = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    fiber = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    sugar = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    sodium = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )

    serving_size = models.CharField(max_length=100)
    serving_unit = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., cup, tbsp, piece")

    # Custom food items
    is_custom = models.BooleanField(default=False, help_text="True if created by user")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_food_items'
    )

    # Meta
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'food_items'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_custom', 'created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.serving_size})"
