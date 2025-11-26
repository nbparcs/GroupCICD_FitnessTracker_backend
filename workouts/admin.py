from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Workout, Goal


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'workout_type', 'workout_date',
        'duration', 'calories_burned', 'status', 'created_at'
    ]
    list_filter = ['workout_type', 'status', 'intensity', 'workout_date']
    search_fields = ['title', 'description', 'user__email']
    date_hierarchy = 'workout_date'
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'workout_type', 'title', 'description')
        }),
        ('Workout Details', {
            'fields': (
                'duration', 'calories_burned', 'distance',
                'intensity', 'status'
            )
        }),
        ('Dates & Times', {
            'fields': (
                'workout_date', 'started_at', 'completed_at',
                'created_at', 'updated_at'
            )
        }),
        ('Additional Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


class ProgressFilter(admin.SimpleListFilter):
    title = 'progress status'
    parameter_name = 'progress'

    def lookups(self, request, model_admin):
        return (
            ('completed', 'Completed'),
            ('in_progress', 'In Progress'),
            ('not_started', 'Not Started'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'completed':
            return queryset.filter(is_completed=True)
        if self.value() == 'in_progress':
            return queryset.filter(is_completed=False, current_value__gt=0)
        if self.value() == 'not_started':
            return queryset.filter(current_value=0)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'user', 'goal_type_display', 'progress_bar', 
        'start_date', 'end_date', 'is_completed_display', 'days_remaining'
    ]
    list_filter = ['goal_type', 'is_completed', ProgressFilter, 'start_date', 'end_date']
    search_fields = ['title', 'notes', 'user__email']
    date_hierarchy = 'end_date'
    readonly_fields = [
        'created_at', 'updated_at', 'completed_at', 
        'progress_percentage', 'is_active'
    ]
    list_per_page = 25

    fieldsets = (
        ('Goal Information', {
            'fields': ('user', 'goal_type', 'title', 'notes')
        }),
        ('Progress Tracking', {
            'fields': (
                'target_value', 'current_value', 'progress_percentage',
                'start_date', 'end_date', 'days_remaining', 'is_active'
            )
        }),
        ('Status', {
            'fields': ('is_completed', 'completed_at')
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def goal_type_display(self, obj):
        return obj.get_goal_type_display()
    goal_type_display.short_description = 'Type'

    def is_completed_display(self, obj):
        return obj.is_completed
    is_completed_display.boolean = True
    is_completed_display.short_description = 'Completed?'

    def progress_bar(self, obj):
        percent = min(100, int((obj.current_value / obj.target_value) * 100)) if obj.target_value > 0 else 0
        color = 'green' if percent >= 90 else 'orange' if percent >= 50 else 'red'
        return format_html(
            '<div style="width:100px; height:20px; border:1px solid #ccc;">'
            '<div style="width:{}%; height:100%; background-color:{};"></div>'
            '<div style="position:relative; top:-20px; text-align:center; color:black; font-size:12px;">{}%</div>'
            '</div>',
            percent, color, percent
        )
    progress_bar.short_description = 'Progress'
    progress_bar.allow_tags = True

    def days_remaining(self, obj):
        return obj.time_remaining
    days_remaining.short_description = 'Days Left'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def save_model(self, request, obj, form, change):
        # If current value reaches or exceeds target, mark as completed
        if obj.current_value >= obj.target_value and not obj.is_completed:
            obj.is_completed = True
        elif obj.current_value < obj.target_value and obj.is_completed:
            obj.is_completed = False
            obj.completed_at = None
        super().save_model(request, obj, form, change)

    class Media:
        css = {
            'all': ['admin/css/goal_progress.css']
        }
