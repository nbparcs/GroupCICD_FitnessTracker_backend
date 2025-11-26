from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from .models import Meal, FoodItem
from .serializers import (
    MealSerializer,
    MealCreateSerializer,
    MealUpdateSerializer,
    NutritionSummarySerializer,
    FoodItemSerializer,
    FoodItemListSerializer
)


class MealViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing meals.
    Provides CRUD operations and additional actions for meal tracking.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'notes']
    ordering_fields = ['meal_date', 'meal_time', 'created_at', 'calories']
    ordering = ['-meal_date', '-meal_time', '-created_at']

    def get_queryset(self):
        """Return meals for the authenticated user only"""
        queryset = Meal.objects.filter(user=self.request.user)

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(meal_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(meal_date__lte=end_date)

        # Filter by meal type
        meal_type = self.request.query_params.get('meal_type')
        if meal_type:
            queryset = queryset.filter(meal_type=meal_type)

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MealCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MealUpdateSerializer
        return MealSerializer

    def perform_create(self, serializer):
        """Associate meal with the authenticated user"""
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a new meal"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Return full meal details
        meal = Meal.objects.get(id=serializer.instance.id)
        response_serializer = MealSerializer(meal)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's meals"""
        today = timezone.now().date()
        meals = self.get_queryset().filter(meal_date=today)
        serializer = self.get_serializer(meals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def yesterday(self, request):
        """Get yesterday's meals"""
        yesterday = timezone.now().date() - timedelta(days=1)
        meals = self.get_queryset().filter(meal_date=yesterday)
        serializer = self.get_serializer(meals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def this_week(self, request):
        """Get this week's meals"""
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        meals = self.get_queryset().filter(
            meal_date__gte=start_of_week,
            meal_date__lte=today
        )
        serializer = self.get_serializer(meals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_date(self, request):
        """Get meals for a specific date"""
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'error': 'Date parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            meal_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        meals = self.get_queryset().filter(meal_date=meal_date)
        serializer = self.get_serializer(meals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get nutrition summary statistics"""
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        queryset = self.get_queryset()

        if start_date:
            queryset = queryset.filter(meal_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(meal_date__lte=end_date)

        # Calculate totals using annotated values
        meals_with_totals = queryset.annotate(
            total_cal=F('calories') * F('servings'),
            total_prot=F('protein') * F('servings'),
            total_carbs=F('carbohydrates') * F('servings'),
            total_fat=F('fats') * F('servings'),
            total_fib=F('fiber') * F('servings'),
            total_sug=F('sugar') * F('servings'),
            total_sod=F('sodium') * F('servings'),
        )

        stats = meals_with_totals.aggregate(
            total_meals=Count('id'),
            total_calories=Sum('total_cal'),
            total_protein=Sum('total_prot'),
            total_carbohydrates=Sum('total_carbs'),
            total_fats=Sum('total_fat'),
            total_fiber=Sum('total_fib'),
            total_sugar=Sum('total_sug'),
            total_sodium=Sum('total_sod'),
            avg_calories=Avg('total_cal'),
        )

        # Get meal type breakdown
        meal_types = queryset.values('meal_type').annotate(
            count=Count('id')
        )
        meal_types_dict = {
            item['meal_type']: item['count']
            for item in meal_types
        }

        # Calculate macros percentage
        total_cal = float(stats['total_calories'] or 0)
        total_prot = float(stats['total_protein'] or 0)
        total_carbs = float(stats['total_carbohydrates'] or 0)
        total_fat = float(stats['total_fats'] or 0)

        if total_cal > 0:
            protein_cal = total_prot * 4
            carbs_cal = total_carbs * 4
            fats_cal = total_fat * 9

            macros_percentage = {
                'protein': round((protein_cal / total_cal) * 100, 1) if protein_cal else 0,
                'carbs': round((carbs_cal / total_cal) * 100, 1) if carbs_cal else 0,
                'fats': round((fats_cal / total_cal) * 100, 1) if fats_cal else 0,
            }
        else:
            macros_percentage = {'protein': 0, 'carbs': 0, 'fats': 0}

        summary_data = {
            'total_meals': stats['total_meals'] or 0,
            'total_calories': stats['total_calories'] or 0,
            'total_protein': stats['total_protein'] or 0,
            'total_carbohydrates': stats['total_carbohydrates'] or 0,
            'total_fats': stats['total_fats'] or 0,
            'total_fiber': stats['total_fiber'] or 0,
            'total_sugar': stats['total_sugar'] or 0,
            'total_sodium': stats['total_sodium'] or 0,
            'avg_calories_per_meal': stats['avg_calories'] or 0,
            'meal_types_breakdown': meal_types_dict,
            'macros_percentage': macros_percentage,
        }

        serializer = NutritionSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily nutrition summary for a date range"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(
            meal_date__gte=start_date,
            meal_date__lte=end_date
        )

        # Group by date and calculate totals
        daily_data = queryset.values('meal_date').annotate(
            total_meals=Count('id'),
            total_calories=Sum(F('calories') * F('servings')),
            total_protein=Sum(F('protein') * F('servings')),
            total_carbohydrates=Sum(F('carbohydrates') * F('servings')),
            total_fats=Sum(F('fats') * F('servings')),
        ).order_by('meal_date')

        return Response(daily_data)


class FoodItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing food items.
    Users can view all food items and create custom ones.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'calories', 'category']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return FoodItemListSerializer
        return FoodItemSerializer

    def get_queryset(self):
        """Return all active food items and user's custom items"""
        # Show all pre-defined items (is_custom=False) and user's custom items
        queryset = FoodItem.objects.filter(
            Q(is_active=True, is_custom=False) | 
            Q(created_by=self.request.user, is_custom=True)
        )

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)

        return queryset

    def perform_create(self, serializer):
        """Set the current user as creator and mark as custom"""
        serializer.save(created_by=self.request.user, is_custom=True)

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of all food categories"""
        categories = FoodItem.objects.filter(
            is_active=True
        ).values_list('category', flat=True).distinct().order_by('category')

        return Response({'categories': list(categories)})


from django.shortcuts import render

# Create your views here.
