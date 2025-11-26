from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
from django.utils import timezone
from decimal import Decimal
from meals.models import Meal

User = get_user_model()

class MealAPITestCase(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a test meal
        self.meal_data = {
            'meal_type': 'breakfast',
            'name': 'Healthy Breakfast',
            'meal_date': '2025-10-31',
            'meal_time': '08:00:00',
            'calories': Decimal('350.00'),
            'protein': Decimal('12.50'),
            'carbohydrates': Decimal('55.00'),
            'fats': Decimal('8.00')
        }
        
        # Create the meal with the correct field names and string values for Decimal fields
        self.meal = Meal.objects.create(
            user=self.user,
            meal_type=self.meal_data['meal_type'],
            name=self.meal_data['name'],
            meal_date=self.meal_data['meal_date'],
            meal_time=self.meal_data['meal_time'],
            calories=self.meal_data['calories'],
            protein=self.meal_data['protein'],
            carbohydrates=self.meal_data['carbohydrates'],
            fats=self.meal_data['fats']
        )
        
        # Set up the client with authentication
        self.client.force_authenticate(user=self.user)
    
    def test_list_meals(self):
        url = reverse('meal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], self.meal.name)
    
    def test_create_meal(self):
        url = reverse('meal-list')
        new_meal = {
            'meal_type': 'lunch',
            'name': 'Lunch Special',
            'meal_date': '2025-11-01',
            'meal_time': '12:30:00',
            'calories': Decimal('400.00'),
            'protein': Decimal('20.00'),
            'carbohydrates': Decimal('50.00'),
            'fats': Decimal('10.00')
        }
        
        response = self.client.post(url, new_meal, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Meal.objects.count(), 2)
        self.assertEqual(Meal.objects.latest('id').name, 'Lunch Special')
    
    def test_retrieve_meal(self):
        url = reverse('meal-detail', args=[self.meal.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.meal.name)
    
    def test_update_meal(self):
        url = reverse('meal-detail', args=[self.meal.id])
        update_data = {
            'calories': Decimal('400.00'),
            'protein': Decimal('15.00')
        }
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.meal.refresh_from_db()
        self.assertEqual(str(self.meal.calories), '400.00')
        self.assertEqual(str(self.meal.protein), '15.00')
    
    def test_delete_meal(self):
        url = reverse('meal-detail', args=[self.meal.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Meal.objects.count(), 0)
    
    def test_meal_validation(self):
        url = reverse('meal-list')
        invalid_data = {
            'meal_type': 'invalid_type',  # Invalid meal type
            'name': 'Invalid Meal',
            'meal_date': '2025-10-31',
            'calories': Decimal('300.00')
        }
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_filter_meals_by_date_range(self):
        # Create a meal for a different date
        Meal.objects.create(
            user=self.user,
            meal_type='lunch',
            name='Lunch Special',
            meal_date='2025-11-01',
            meal_time='12:30:00',
            calories='500.00',
            protein='25.00',
            carbohydrates='60.00',
            fats='15.00'
        )
        
        # Filter by date range
        url = f"{reverse('meal-list')}?start_date=2025-10-30&end_date=2025-10-31"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the original meal
        self.assertEqual(response.data[0]['name'], 'Healthy Breakfast')
    
    def test_filter_meals_by_type(self):
        # Create a meal of different type
        Meal.objects.create(
            user=self.user,
            meal_type='lunch',
            name='Lunch Special',
            meal_date='2025-10-31',
            meal_time='12:30:00',
            calories='500.00',
            protein='25.00',
            carbohydrates='60.00',
            fats='15.00'
        )
        
        # Filter by meal type
        url = f"{reverse('meal-list')}?meal_type=breakfast"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['meal_type'], 'breakfast')
    
    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        url = reverse('meal-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_minimal_meal(self):
        url = reverse('meal-list')
        minimal_data = {
            'meal_type': 'snack',
            'name': 'Afternoon Snack',
            'meal_date': '2025-11-01',
            'calories': Decimal('150.00')
        }
        response = self.client.post(url, minimal_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Meal.objects.count(), 2)
        self.assertEqual(Meal.objects.latest('id').name, 'Afternoon Snack')
