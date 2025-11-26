from django.contrib import admin
from .models import Meal, FoodItem


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'user', 'meal_type', 'meal_date', 'meal_time',
        'calories', 'protein', 'carbohydrates', 'fats', 'servings'
    ]
    list_filter = ['meal_type', 'meal_date', 'user']
    search_fields = ['name', 'description', 'user__email']
    date_hierarchy = 'meal_date'
    readonly_fields = ['created_at', 'updated_at', 'total_calories',
                       'total_protein', 'total_carbohydrates', 'total_fats']

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'meal_type', 'name', 'description')
        }),
        ('Nutritional Information (per serving)', {
            'fields': (
                'calories', 'protein', 'carbohydrates', 'fats',
                'fiber', 'sugar', 'sodium'
            )
        }),
        ('Serving Information', {
            'fields': ('serving_size', 'servings')
        }),
        ('Calculated Totals', {
            'fields': (
                'total_calories', 'total_protein',
                'total_carbohydrates', 'total_fats'
            ),
            'classes': ('collapse',)
        }),
        ('Date & Time', {
            'fields': ('meal_date', 'meal_time')
        }),
        ('Additional Information', {
            'fields': ('notes', 'photo_url', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'calories', 'protein',
        'carbohydrates', 'fats', 'serving_size', 'is_active'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description', 'category']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'is_active')
        }),
        ('Nutritional Information (per serving)', {
            'fields': (
                'calories', 'protein', 'carbohydrates', 'fats',
                'fiber', 'sugar', 'sodium'
            )
        }),
        ('Serving Information', {
            'fields': ('serving_size',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


from django.contrib import admin

# Register your models here.
