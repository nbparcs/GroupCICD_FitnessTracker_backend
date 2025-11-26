from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Workout, Goal
from .serializers import (
    WorkoutSerializer,
    WorkoutCreateSerializer,
    WorkoutUpdateSerializer,
    WorkoutSummarySerializer,
    GoalSerializer
)


class WorkoutViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing workouts.
    Provides CRUD operations and additional actions for workout tracking.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'notes']
    ordering_fields = ['workout_date', 'created_at', 'duration', 'calories_burned']
    ordering = ['-workout_date', '-created_at']

    def get_queryset(self):
        """Return workouts for the authenticated user only"""
        queryset = Workout.objects.filter(user=self.request.user)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(workout_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(workout_date__lte=end_date)

        # Filter by workout type
        workout_type = self.request.query_params.get('workout_type')
        if workout_type:
            queryset = queryset.filter(workout_type=workout_type)

        # Filter by status
        workout_status = self.request.query_params.get('status')
        if workout_status:
            queryset = queryset.filter(status=workout_status)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return WorkoutCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return WorkoutUpdateSerializer
        return WorkoutSerializer

    def perform_create(self, serializer):
        """Associate workout with the authenticated user"""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a new workout"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Get the created instance from the serializer
        instance = serializer.instance
        
        # If we have an instance with an ID, return its full details
        if instance and hasattr(instance, 'id'):
            response_serializer = WorkoutSerializer(instance)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        # Fallback to returning the validated data
        return Response(
            serializer.validated_data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's workouts"""
        today = timezone.now().date()
        workouts = self.get_queryset().filter(workout_date=today)
        serializer = self.get_serializer(workouts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def this_week(self, request):
        """Get this week's workouts"""
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        workouts = self.get_queryset().filter(
            workout_date__gte=start_of_week,
            workout_date__lte=today
        )
        serializer = self.get_serializer(workouts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get workout summary statistics"""
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        queryset = self.get_queryset()

        if start_date:
            queryset = queryset.filter(workout_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(workout_date__lte=end_date)

        # Calculate statistics
        stats = queryset.aggregate(
            total_workouts=Count('id'),
            total_duration=Sum('duration'),
            total_calories=Sum('calories_burned'),
            total_distance=Sum('distance'),
            completed_workouts=Count('id', filter=Q(status='completed'))
        )

        # Get workout type breakdown
        workout_types = queryset.values('workout_type').annotate(
            count=Count('id')
        )
        workout_types_dict = {
            item['workout_type']: item['count']
            for item in workout_types
        }

        summary_data = {
            'total_workouts': stats['total_workouts'] or 0,
            'total_duration': stats['total_duration'] or 0,
            'total_calories': stats['total_calories'] or 0,
            'total_distance': stats['total_distance'] or 0,
            'completed_workouts': stats['completed_workouts'] or 0,
            'workout_types': workout_types_dict
        }

        serializer = WorkoutSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Mark workout as started"""
        workout = self.get_object()

        if workout.status == 'completed':
            return Response(
                {'error': 'Cannot start a completed workout'},
                status=status.HTTP_400_BAD_REQUEST
            )

        workout.status = 'in_progress'
        workout.started_at = timezone.now()
        workout.save()

        serializer = self.get_serializer(workout)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark workout as completed"""
        workout = self.get_object()

        if workout.status == 'completed':
            return Response(
                {'error': 'Workout is already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get optional data from request
        duration = request.data.get('duration', workout.duration)
        calories = request.data.get('calories_burned', workout.calories_burned)
        distance = request.data.get('distance', workout.distance)

        workout.status = 'completed'
        workout.completed_at = timezone.now()

        if duration:
            workout.duration = duration
        if calories:
            workout.calories_burned = calories
        if distance:
            workout.distance = distance

        workout.save()

        serializer = self.get_serializer(workout)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def skip(self, request, pk=None):
        """Mark workout as skipped"""
        workout = self.get_object()

        if workout.status == 'completed':
            return Response(
                {'error': 'Cannot skip a completed workout'},
                status=status.HTTP_400_BAD_REQUEST
            )

        workout.status = 'skipped'
        workout.save()

        serializer = self.get_serializer(workout)
        return Response(serializer.data)


class GoalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing fitness goals.
    Provides CRUD operations for user's fitness goals.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = GoalSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'notes']
    ordering_fields = ['end_date', 'start_date', 'created_at', 'target_value']
    ordering = ['-end_date', '-created_at']

    def get_queryset(self):
        """Return goals for the authenticated user only"""
        queryset = Goal.objects.filter(user=self.request.user)

        # Filter by completion status
        is_completed = self.request.query_params.get('is_completed')
        if is_completed is not None:
            is_completed = is_completed.lower() == 'true'
            queryset = queryset.filter(is_completed=is_completed)

        # Filter by goal type
        goal_type = self.request.query_params.get('goal_type')
        if goal_type:
            queryset = queryset.filter(goal_type=goal_type)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(end_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(start_date__lte=end_date)

        # Filter active goals (current date is between start and end date)
        active = self.request.query_params.get('active')
        if active is not None:
            today = timezone.now().date()
            if active.lower() == 'true':
                queryset = queryset.filter(
                    start_date__lte=today,
                    end_date__gte=today,
                    is_completed=False
                )
            else:
                queryset = queryset.exclude(
                    start_date__lte=today,
                    end_date__gte=today,
                    is_completed=False
                )

        return queryset

    def perform_create(self, serializer):
        """Set the current user as the goal owner"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """Update the current progress of a goal"""
        goal = self.get_object()
        current_value = request.data.get('current_value')
        increment_by = request.data.get('increment_by')

        if current_value is not None:
            try:
                goal.current_value = float(current_value)
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid current_value provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif increment_by is not None:
            try:
                goal.current_value += float(increment_by)
            except (TypeError, ValueError):
                return Response(
                    {'error': 'Invalid increment_by value provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {'error': 'Either current_value or increment_by must be provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save the goal to trigger any automatic updates (like completion)
        goal.save()
        serializer = self.get_serializer(goal)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for user's goals"""
        user_goals = Goal.objects.filter(user=request.user)
        
        total_goals = user_goals.count()
        completed_goals = user_goals.filter(is_completed=True).count()
        in_progress_goals = user_goals.filter(is_completed=False).count()
        
        # Get goals by type
        goals_by_type = user_goals.values('goal_type').annotate(
            count=Count('id'),
            completed=Count('id', filter=Q(is_completed=True)),
            in_progress=Count('id', filter=Q(is_completed=False))
        )
        
        # Calculate completion rate
        completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0
        
        return Response({
            'total_goals': total_goals,
            'completed_goals': completed_goals,
            'in_progress_goals': in_progress_goals,
            'completion_rate': round(completion_rate, 2),
            'goals_by_type': goals_by_type
        })


from django.shortcuts import render
