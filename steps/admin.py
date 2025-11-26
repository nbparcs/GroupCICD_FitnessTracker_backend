from django.contrib import admin
from .models import DailySteps, StepGoal, StepStreak


@admin.register(StepGoal)
class StepGoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_goal', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DailySteps)
class DailyStepsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'steps', 'distance_km', 'calories_burned',
        'goal_achieved', 'source', 'created_at'
    ]
    list_filter = ['date', 'source', 'created_at']
    search_fields = ['user__username', 'user__email', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'goal_achieved', 'goal_percentage']
    date_hierarchy = 'date'
    ordering = ['-date']

    fieldsets = (
        ('User & Date', {
            'fields': ('user', 'date', 'source')
        }),
        ('Step Data', {
            'fields': ('steps', 'distance_km', 'calories_burned', 'active_minutes')
        }),
        ('Goal Progress', {
            'fields': ('goal_achieved', 'goal_percentage'),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StepStreak)
class StepStreakAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'current_streak', 'longest_streak',
        'total_days_goal_met', 'last_updated'
    ]
    list_filter = ['last_updated', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']

    actions = ['update_streaks']

    def update_streaks(self, request, queryset):
        for streak in queryset:
            streak.update_streak()
        self.message_user(request, f"Updated {queryset.count()} streak(s)")

    update_streaks.short_description = "Update selected streaks"


from django.contrib import admin

# Register your models here.
