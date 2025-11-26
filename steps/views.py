from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Avg, Max, Count, Q
from django.utils import timezone
from datetime import date, timedelta, datetime
from .models import DailySteps, StepGoal, StepStreak
from .serializers import (
    DailyStepsSerializer, StepGoalSerializer, StepStreakSerializer,
    StepSummarySerializer, WeeklyStepsSerializer
)


class StepGoalViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user's step goals"""
    serializer_class = StepGoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StepGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Check if user already has a goal
        existing_goal = StepGoal.objects.filter(user=request.user).first()
        if existing_goal:
            # Update existing goal instead of creating new one
            serializer = self.get_serializer(existing_goal, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's step goal"""
        goal, created = StepGoal.objects.get_or_create(
            user=request.user,
            defaults={'daily_goal': 10000}
        )
        serializer = self.get_serializer(goal)
        return Response(serializer.data)


class DailyStepsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing daily step records"""
    serializer_class = DailyStepsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['date', 'steps', 'distance_km', 'calories_burned']
    ordering = ['-date']
    search_fields = ['notes', 'source']

    def get_queryset(self):
        queryset = DailySteps.objects.filter(user=self.request.user)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)

        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)

        # Filter by goal achievement
        goal_achieved = self.request.query_params.get('goal_achieved')
        if goal_achieved is not None:
            try:
                goal = self.request.user.step_goal.daily_goal
                if goal_achieved.lower() == 'true':
                    queryset = queryset.filter(steps__gte=goal)
                else:
                    queryset = queryset.filter(steps__lt=goal)
            except StepGoal.DoesNotExist:
                pass

        return queryset

    def perform_create(self, serializer):
        step_record = serializer.save(user=self.request.user)

        # Update streak if record is for yesterday or today
        if step_record.date >= date.today() - timedelta(days=1):
            streak, created = StepStreak.objects.get_or_create(user=self.request.user)
            streak.update_streak()

    def perform_update(self, serializer):
        step_record = serializer.save()

        # Update streak if record is for yesterday or today
        if step_record.date >= date.today() - timedelta(days=1):
            streak, created = StepStreak.objects.get_or_create(user=self.request.user)
            streak.update_streak()

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's step record"""
        today = date.today()
        try:
            steps = DailySteps.objects.get(user=request.user, date=today)
            serializer = self.get_serializer(steps)
            return Response(serializer.data)
        except DailySteps.DoesNotExist:
            return Response(
                {'detail': 'No steps recorded for today'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def quick_log(self, request):
        """Quick log steps for today"""
        today = date.today()
        steps = request.data.get('steps')

        if not steps:
            return Response(
                {'error': 'Steps value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Update if exists, create if not
            step_record, created = DailySteps.objects.update_or_create(
                user=request.user,
                date=today,
                defaults={
                    'steps': steps,
                    'source': request.data.get('source', 'manual')
                }
            )

            # Update streak
            streak, _ = StepStreak.objects.get_or_create(user=request.user)
            streak.update_streak()

            serializer = self.get_serializer(step_record)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get current week's step data"""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        steps_data = DailySteps.objects.filter(
            user=request.user,
            date__range=[week_start, week_end]
        ).order_by('date')

        # Create full week data with zeros for missing days
        week_data = []
        current_date = week_start
        steps_dict = {s.date: s for s in steps_data}

        try:
            goal = request.user.step_goal.daily_goal
        except StepGoal.DoesNotExist:
            goal = 10000

        while current_date <= week_end:
            step_record = steps_dict.get(current_date)
            week_data.append({
                'date': current_date,
                'steps': step_record.steps if step_record else 0,
                'goal_achieved': step_record.steps >= goal if step_record else False,
                'day_name': current_date.strftime('%A')
            })
            current_date += timedelta(days=1)

        serializer = WeeklyStepsSerializer(week_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get current month's step data"""
        today = date.today()
        month_start = today.replace(day=1)

        # Get next month's first day, then subtract one day
        if today.month == 12:
            month_end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        steps_data = DailySteps.objects.filter(
            user=request.user,
            date__range=[month_start, month_end]
        ).order_by('date')

        serializer = self.get_serializer(steps_data, many=True)

        # Calculate monthly summary
        total_steps = sum(s.steps for s in steps_data)
        days_recorded = steps_data.count()
        avg_steps = total_steps / days_recorded if days_recorded > 0 else 0

        return Response({
            'month': today.strftime('%B %Y'),
            'start_date': month_start,
            'end_date': month_end,
            'total_steps': total_steps,
            'days_recorded': days_recorded,
            'average_steps': round(avg_steps),
            'daily_data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get comprehensive step statistics"""
        # Get date range from query params or default to last 30 days
        end_date = date.today()
        period = request.query_params.get('period', '30')  # days

        try:
            days = int(period)
            start_date = end_date - timedelta(days=days - 1)
        except ValueError:
            return Response(
                {'error': 'Invalid period parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get step records for the period
        steps_data = DailySteps.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        )

        if not steps_data.exists():
            return Response({
                'message': 'No step data available for this period',
                'total_steps': 0,
                'days_recorded': 0
            })

        # Calculate statistics
        aggregates = steps_data.aggregate(
            total_steps=Sum('steps'),
            total_distance=Sum('distance_km'),
            total_calories=Sum('calories_burned'),
            total_active_minutes=Sum('active_minutes'),
            average_steps=Avg('steps'),
            average_distance=Avg('distance_km'),
            average_calories=Avg('calories_burned'),
            max_steps=Max('steps')
        )

        # Get highest step day
        highest_day = steps_data.order_by('-steps').first()

        # Calculate goal achievement
        try:
            goal = request.user.step_goal.daily_goal
            days_goal_met = steps_data.filter(steps__gte=goal).count()
        except StepGoal.DoesNotExist:
            goal = 10000
            days_goal_met = 0

        days_recorded = steps_data.count()
        goal_rate = (days_goal_met / days_recorded * 100) if days_recorded > 0 else 0

        # Get streak info
        streak, _ = StepStreak.objects.get_or_create(user=request.user)

        summary_data = {
            'total_steps': aggregates['total_steps'] or 0,
            'total_distance_km': round(float(aggregates['total_distance'] or 0), 2),
            'total_calories': aggregates['total_calories'] or 0,
            'total_active_minutes': aggregates['total_active_minutes'] or 0,
            'average_steps': round(aggregates['average_steps'] or 0),
            'average_distance_km': round(float(aggregates['average_distance'] or 0), 2),
            'average_calories': round(aggregates['average_calories'] or 0),
            'days_recorded': days_recorded,
            'days_goal_met': days_goal_met,
            'goal_achievement_rate': round(goal_rate, 1),
            'highest_steps': aggregates['max_steps'] or 0,
            'highest_steps_date': highest_day.date if highest_day else None,
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
        }

        serializer = StepSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def chart_data(self, request):
        """Get data formatted for charts"""
        period = request.query_params.get('period', '7')  # days

        try:
            days = int(period)
            end_date = date.today()
            start_date = end_date - timedelta(days=days - 1)
        except ValueError:
            return Response(
                {'error': 'Invalid period parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get step records
        steps_data = DailySteps.objects.filter(
            user=request.user,
            date__range=[start_date, end_date]
        ).order_by('date')

        # Create full range data with zeros for missing days
        chart_data = []
        current_date = start_date
        steps_dict = {s.date: s for s in steps_data}

        try:
            goal = request.user.step_goal.daily_goal
        except StepGoal.DoesNotExist:
            goal = 10000

        while current_date <= end_date:
            step_record = steps_dict.get(current_date)
            chart_data.append({
                'date': current_date.isoformat(),
                'steps': step_record.steps if step_record else 0,
                'distance_km': float(step_record.distance_km) if step_record and step_record.distance_km else 0,
                'calories': step_record.calories_burned if step_record else 0,
                'goal': goal,
                'goal_achieved': step_record.steps >= goal if step_record else False
            })
            current_date += timedelta(days=1)

        return Response({
            'period_days': days,
            'start_date': start_date,
            'end_date': end_date,
            'goal': goal,
            'data': chart_data
        })


class StepStreakViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing step streaks"""
    serializer_class = StepStreakSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StepStreak.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's streak"""
        streak, created = StepStreak.objects.get_or_create(user=request.user)
        streak.update_streak()
        serializer = self.get_serializer(streak)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """Manually refresh streak calculation"""
        streak, created = StepStreak.objects.get_or_create(user=request.user)
        streak.update_streak()
        serializer = self.get_serializer(streak)
        return Response(serializer.data)


from django.shortcuts import render

# Create your views here.
